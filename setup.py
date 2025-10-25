from setuptools import find_packages
from setuptools import setup
from setuptools.command.test import test
import os


def read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return f.read()


version = '0.1'
shortdesc = 'Firebase integration for cone.app'
longdesc = '\n\n'.join([read_file(name) for name in [
    'README.rst',
    'CHANGES.rst',
    'LICENSE.rst'
]])


class Test(test):

    def run_tests(self):
        from cone.firebase import tests
        tests.run_tests()


setup(
    name='cone.firebase',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        'Environment :: Web Environment',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    keywords='node pyramid cone web',
    author='Cone Contributors',
    author_email='dev@conestack.org',
    url='http://github.com/conestack/cone.firebase',
    license='Simplified BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['cone'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'proto-plus==1.18.1',
        'google-api-core==1.26.3',
        'google-api-python-client==2.2.0',
        'google-auth==1.29.0',
        'google-auth-httplib2==0.1.0',
        'google-auth-oauthlib==0.4.6',
        'google-cloud-core==1.6.0',
        'google-cloud-firestore==2.1.0',
        'google-cloud-storage==1.37.1',
        'google-crc32c==1.1.2',
        'google-pasta==0.2.0',
        'google-resumable-media==1.2.0',
        'googleapis-common-protos==1.53.0',

        'setuptools',
        'cone.app<1.1.0',
        'requests',
        'firebase_admin==4.5.3',
        # 'protobuf==3.15.8'
    ],
    extras_require=dict(test=['zope.testrunner']),
    tests_require=['zope.testrunner'],
    cmdclass=dict(test=Test)
)
