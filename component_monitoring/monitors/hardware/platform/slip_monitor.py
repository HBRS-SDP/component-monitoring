from component_monitoring.monitor_base import MonitorBase
from multiprocessing import Process
from hmmlearn.hmm import MultinomialHMM

from ropod_ros_msgs.msg import StateInfo, Status
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32

import rospy
import numpy as np

class SlipMonitor(MonitorBase):
    def __init__(self, config_params, black_box_comm):
        super(SlipMonitor, self).__init__(config_params, black_box_comm)
        
        self.use_back_scans = True
        self.initialized, self.back_initialized = True, True
        self.num_scans, self.num_back_scans = None, None
        self.make_predictions = True
        self.verbose = False

        self.use_HMM = config_params.arguments.get('use_HMM', False)
        self.laser_scan_topic = config_params.arguments.get('laser_scan_topic_name', 
                                                            '/projected_scan_front')
        self.back_laser_scan_topic = config_params.arguments.get('back_laser_scan_topic_name', 
                                                            '/projected_scan_back')
        self.odometry_topic = config_params.arguments.get('odometry_topic_name', 
                                                        '/ropod/odom_')

        self.laser_scan_decision_threshold = 9.0
        self.back_laser_scan_decision_threshold = 3.0   # Require validation, after removing filtration
        self.odometry_vel_decision_threshold = 0.15

        self.previous_laser_scan_msg = None
        self.latest_laser_scan_msg = None
        self.previous_odometry_msg_vel = None
        self.latest_odometry_msg_vel = None
        self.previous_back_laser_scan_msg = None
        self.latest_back_laser_scan_msg = None

        self.change_queue_length = 10
        self.laser_scan_diff_queue = np.zeros(self.change_queue_length)
        self.back_laser_scan_diff_queue = np.zeros(self.change_queue_length)
        self.odometry_vel_queue = np.zeros(self.change_queue_length)

        self.node_initialised = False
        self.slip_detected = False

        self._init_debugging_publishers()
        if self.use_HMM: self._init_HMM()

    def get_status(self):
        try:
            rospy.get_master().getPid()
            if not self.node_initialised:
                self.node_thread = Process(target=self._init_node_and_subscribers)
                self.node_thread.start()
                self.node_initialised = True
        except:
            if self.node_initialised:
                rosnode.kill_nodes('slip_monitor')
                self.node_thread.terminate()
            self.node_initialised = False

        status_msg = self.get_status_message_template()
        status_msg["monitorName"] = self.config_params.name
        status_msg["monitorDescription"] = self.config_params.description
        self._get_slip_status()
        status_msg["healthStatus"] = dict()
        status_msg["healthStatus"]["status"] = self.slip_detected
        return status_msg

    def laser_scan_cb(self, msg):
        self.previous_laser_scan_msg = np.copy(self.latest_laser_scan_msg)
        if self.use_2D_laser:
            # Process out-of-range measurements: inf --> 0.:
            self.latest_laser_scan_msg = np.array([x if not np.isinf(x) else 0. for x in msg.ranges])
        else:
            # Process very close  measurements: max_value --> 0.:
            # self.latest_laser_scan_msg = np.array([x if x!=msg.range_max else 0. for x in msg.ranges])
            self.latest_laser_scan_msg = np.array(msg.ranges)
        
        if not self.initialized:
            self.num_scans = len(msg.ranges)
            self.initialized = True

    def back_laser_scan_cb(self, msg):
        self.previous_back_laser_scan_msg = np.copy(self.latest_back_laser_scan_msg)
        
        # Process very close measurements: max_value or 0. --> 0.4:
        self.latest_back_laser_scan_msg = np.array([x if (x!=msg.range_max or x!=0.) else 0.4 for x in msg.ranges])
        
        if not self.back_initialized:
            self.num_back_scans = len(msg.ranges)
            self.back_initialized = True

    def odometry_cb(self, msg):
        self.previous_odometry_msg_vel = np.copy(self.latest_odometry_msg_vel)

        self.latest_odometry_msg_vel = np.array([msg.twist.twist.linear.x,
                                                 msg.twist.twist.linear.y,
                                                 msg.twist.twist.linear.z])

    def _get_slip_status(self):
        outlier_removal_threshold = 0.1

        # Process laser sensor measurements:
        reliable_scan_indices = np.where(abs(self.latest_laser_scan_msg - self.previous_laser_scan_msg) < outlier_removal_threshold)
        normed_laser_scan_diff = np.linalg.norm((self.latest_laser_scan_msg[reliable_scan_indices] - self.previous_laser_scan_msg[reliable_scan_indices]), 1)
        self.laser_scan_diff_queue = self._update_queue(self.laser_scan_diff_queue, normed_laser_scan_diff)
        
        # Process back (projected_scan)laser sensor measurements: 
        reliable_back_scan_indices = np.where(abs(self.latest_back_laser_scan_msg - self.previous_back_laser_scan_msg) < outlier_removal_threshold)
        normed_back_laser_scan_diff = np.linalg.norm((self.latest_back_laser_scan_msg[reliable_back_scan_indices] - self.previous_back_laser_scan_msg[reliable_back_scan_indices]), 1)
        self.back_laser_scan_diff_queue = self._update_queue(self.back_laser_scan_diff_queue, normed_back_laser_scan_diff)

        # Process odometry velocity values, instead of differences:
        normed_odometry_vel = np.linalg.norm(self.latest_odometry_msg_vel)
        self.odometry_vel_queue = self._update_queue(self.odometry_vel_queue, normed_odometry_vel)

        if self.use_HMM:
            # Determine if a slip event has most likely occurred with a discretized HMM.
            # Define values at which each measurement indicates a significant 'change':
            obs_sequence_length = self.change_queue_length
            observation_sequence = np.zeros((obs_sequence_length, 1), dtype=int)

            for i in range(obs_sequence_length):
                observation = 99
                
                if self.use_back_scans:
                    back_laser_diff_conditions = (self.back_laser_scan_diff_queue[i] < self.back_laser_scan_decision_threshold,
                                                  self.back_laser_scan_diff_queue[i] > self.back_laser_scan_decision_threshold)
                else:
                    back_laser_diff_conditions = (0, 0)

                if (self.laser_scan_diff_queue[i] < self.laser_scan_decision_threshold or \
                    back_laser_diff_conditions[0]) and \
                    self.odometry_vel_queue[i] < self.odometry_vel_decision_threshold:
                    # Constant laser sensor and odometry measurements
                    observation = 0
                elif (self.laser_scan_diff_queue[i] > self.laser_scan_decision_threshold or \
                     back_laser_diff_conditions[1]) and \
                     self.odometry_vel_queue[i] < self.odometry_vel_decision_threshold: 
                    # Changing laser sensor and constant odometry measurements
                    observation = 1
                elif (self.laser_scan_diff_queue[i] < self.laser_scan_decision_threshold or \
                     back_laser_diff_conditions[0]) and \
                     self.odometry_vel_queue[i] > self.odometry_vel_decision_threshold: 
                    # Constant laser sensor and changing odometry measurements
                    observation = 2
                elif (self.laser_scan_diff_queue[i] > self.laser_scan_decision_threshold or \
                      back_laser_diff_conditions[1]) and \
                      self.odometry_vel_queue[i] > self.odometry_vel_decision_threshold: 
                    # Changing laser sensor and odometry measurements
                    observation = 3
                observation_sequence[i] = observation

            log_prob, hidden_state_sequence = self.HMM.decode(observation_sequence, 
                                                              algorithm='viterbi')
            hidden_state_sequence = [self.possible_states[i] for i in hidden_state_sequence]

            # Check estimated hidden state for the first 4 states in the
            # sequence:    
            if self.make_predictions and np.count_nonzero(self.laser_scan_diff_queue == 0.) < 3 and np.count_nonzero(self.odometry_vel_queue == 0.) < 3:
                if np.all(np.array(hidden_state_sequence[:4]) == self.possible_states[0]):
                    self.slip_detected = True
                    # print('\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    # rospy.loginfo('[slip_detector] Slip event detected!!!')
                    
                    state_info_msg = StateInfo()
                    state_info_msg.state = StateInfo.ERROR
                    self.sound_pub.publish(state_info_msg)
                    rospy.sleep(0.1)
                else:
                    self.slip_detected = False
        else:        
            laser_scan_change_measure = np.average(self.laser_scan_diff_queue)
            odometry_vel_change_measure = np.average(self.odometry_vel_queue)

            if np.count_nonzero(self.laser_scan_diff_queue == 0.) < 3 and np.count_nonzero(self.odometry_pos_diff_queue == 0.) < 3:
                # Determine if a slip event has most likely occurred with a simple heuristic.
                if laser_scan_change_measure < self.laser_scan_decision_threshold and \
                    odometry_vel_change_measure > self.odometry_pos_decision_threshold:
                    self.slip_detected = True
                    # print('\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                    # rospy.loginfo('[slip_detector] Slip event detected!!!')
                else:
                    self.slip_detected = False
    
    def _init_node_and_subscribers(self):
        rospy.init_node('slip_monitor', disable_signals=True)

        self.laser_scan_sub = rospy.Subscriber(self.laser_scan_topic,
                                               LaserScan,
                                               self.laser_scan_cb)

        self.back_laser_scan_sub = rospy.Subscriber(self.back_laser_scan_topic,
                                                    LaserScan,
                                                    self.back_laser_scan_cb)
        
        self.odometry_sub = rospy.Subscriber(self.odometry_topic,
                                             Odometry,
                                             self.odometry_cb)
        
        try:
            while not rospy.is_shutdown():
                rospy.sleep(0.1)
        except Exception as exc:
            rospy.logerr(str(exc))

    def _init_debugging_publishers(self):
        self.sound_pub = rospy.Publisher('/ropod/state_info', StateInfo, queue_size=10)

    def _init_HMM(self):
        rospy.loginfo('[slip_detector] Instantiating HMM...')
        self.possible_states = ['slip', 'no_slip']

        # Define initial state, state transition, and observation probabilities:
        initial_state_dist = np.array([0.2, 0.8])

        state_trans_probs = np.array([[0.5, 0.5],
                                      [0.3, 0.7]])

        observation_probs = np.array([[0.1, 0.1, 0.8, 0.0],
                                      [0.1, 0.1, 0.2, 0.6]])

        # Instantiate the model:
        self.HMM = MultinomialHMM(n_components=len(self.possible_states))
        self.HMM.startprob_ = initial_state_dist
        self.HMM.transmat_ = state_trans_probs
        self.HMM.emissionprob_ = observation_probs

    def _update_queue(self, queue_array, value):
        queue_array = np.roll(queue_array, 1)
        queue_array[0] = value

        return queue_array