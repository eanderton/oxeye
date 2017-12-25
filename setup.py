import setuptools
from oxeye.version import __VERSION__


setuptools.setup(name='oxeye',
                 version=__VERSION__,
                 description='Oxeye Parser Library', 
                 long_description=open('README.md').read().strip(),
                 author='Eric Anderton',
                 author_email='eric.t.anderton@gmail.com',
                 url='http://github.com/eanderton/oxeye',
                 packages=['oxeye'],
                 install_requires=[],
                 license='MIT License',
                 zip_safe=False,
                 keywords='parser parsers dfa lexer lexers',
                 classifiers=['Packages'])
