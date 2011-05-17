#!/usr/bin/env python
""" Setup file for PyFoo package """
 
from distutils.core import setup
setup(
	name='gitosis-admin',
	version='0.1',
	description='Gitosis remote repository admin tool',
	long_description = "Gitosis remote repository admin tool",
	author='SevenQuark',
	author_email='sevenquark@gmail.com',
	url='http://www.sevenquark.com/',
	packages=[ 'gitosisadmin', ],
 
	classifiers=(
		'Development Status :: 2 - Pre-Alpha',
		'Environment :: Console',
		'License :: OSI Approved :: GNU General Public License (GPL)',
		'Operating System :: POSIX',
		'Operating System :: Unix',
		'Programming Language :: Python',
	),

	license="GPL-2"
)
