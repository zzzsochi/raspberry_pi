from setuptools import setup, find_packages


setup(name='mpd_ctrl',
      version='1.0',
      description='controller for mpd',
      # long_description=README,
      classifiers=[
          "License :: OSI Approved :: BSD License",
          "Operating System :: POSIX",
          "Programming Language :: Python :: 3.4",
          "Topic :: Internet :: WWW/HTTP",
      ],
      author='Alexander Zelenyak',
      author_email='zzz.sochi@gmail.com',
      url='',
      keywords='mpd',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'aiohttp',
          'aiompd',
          'zope.dottedname',
      ],  # 'quick2wire'],
      entry_points={
          'console_scripts': [
              'zr = zr'
          ],
      },
)
