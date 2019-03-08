from setuptools import setup, find_packages

setup(name='verifai',
      install_requires=[
          'numpy',
          'scipy',
          'pulp',
          'dotmap',
          'metric-temporal-logic',
          'matplotlib',
          'easydict',
          'joblib',
          'dill',
          'pyglet',
          'future',
          'pandas',
          'scikit-learn',
          'scenic @ git+https://github.com/BerkeleyLearnVerify/Scenic.git#egg=scenic',
      ],
      python_requires='>=3.6',
      packages=find_packages(),
      package_data={
        '': ['*.sc', '*.wbt'],   # include Scenic and Webots files
      },
)
