import setuptools
import subprocess
from setuptools.command.develop import develop
from oxeye.version import __VERSION__

# shim to install dev depenedencies on 'setup.py develop'
class ExtDevelop(develop):
    def install_for_development(self):
        from distutils import log
        develop.install_for_development(self)
        if 'develop' in self.distribution.extras_require:
            log.info('\nInstalling development dependencies')
            requirements = ' '.join(self.distribution.extras_require['develop'])
            proc = subprocess.Popen('pip install ' + requirements, shell=True)
            proc.wait()


setuptools.setup(
    name='oxeye',
    version=__VERSION__,
    description='Oxeye Parser Library',
    long_description=open('README.md').read().strip(),
    author='Eric Anderton',
    author_email='eric.t.anderton@gmail.com',
    url='http://github.com/eanderton/oxeye',
    packages=['oxeye'],
    test_suite='tests',
    install_requires=[
        'pragma_utils',
    ],
    extras_require={
       'develop': [
           'pytest',
           'pytest-cov',
       ],
    },
    cmdclass= {
       'develop': ExtDevelop,
    },
    license='MIT License',
    zip_safe=False,
    keywords='parser parsers dfa lexer lexers',
    classifiers=[
        'Packages'
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ])
