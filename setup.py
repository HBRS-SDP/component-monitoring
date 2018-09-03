from setuptools import setup, find_packages

setup(name='component_monitoring',
      version='1.0.0',
      description='A robot component monitoring library',
      url='https://github.com/ropod-project/component-monitoring',
      author='Alex Mitrevski, Santosh Thoduka',
      author_email='aleksandar.mitrevski@h-brs.de, santosh.thoduka@h-brs.de',
      keywords='component_monitoring fault_detection robotics',
      packages=find_packages(exclude=['contrib', 'docs', 'tests']),
      project_urls={
          'Source': 'https://github.com/ropod-project/component-monitoring'
      })
