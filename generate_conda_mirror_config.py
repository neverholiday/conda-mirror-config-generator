#!/usr/bin/env python3
#
# Copyright (C) 2023
#			Written by Nasrun (Nas) Hayeeyama
#

VERSIONNUMBER = 'v1.0'
PROGRAM_DESCRIPTION = "For generate conda mirror configuration yaml"

########################################################
#
#	STANDARD IMPORTS
#

import os

import json
import yaml

import argparse

import subprocess
import shlex

########################################################
#
#	LOCAL IMPORTS
#

########################################################
#
#	Standard globals
#

########################################################
#
#	Program specific globals
#

DefaultPackageToMirrorPath = '/etc/conda_mirror/package_config.json'
DefaultYamlMirrorConfigDirectoryPath = '/var/lib/conda_mirror'

########################################################
#
#	Helper functions
#

def saveFileYml( fileName, dataList ):
	'''	Save package list to format file yaml
	'''

	# construct yaml dict
	yamlDict = { 'blacklist' : [ { 'name' : '*' } ],
				'whitelist' : [] }

	# open file and dump list of data in yaml format
	with open( fileName, 'w' ) as f:
		yamlDict[ 'whitelist' ] = dataList
		yaml.dump( yamlDict, f )

########################################################
#
#	Class definitions
#

########################################################
#
#	Function bodies
#

########################################################
#
#	main
#	
def main():
	
	# initial parser instance
	parser = argparse.ArgumentParser( description=PROGRAM_DESCRIPTION )

	# add arguments and option here
	parser.add_argument( '--packageConfigPath', dest='packageConfigPath', 
					 		type=str, 
					 		default=DefaultPackageToMirrorPath,
					 		help='Package list to be mirror configuration path' )
	
	parser.add_argument( '--yamlOutputDirectoryPath',
		     				dest='yamlOutputDirectoryPath',
							type=str,
							default=DefaultYamlMirrorConfigDirectoryPath,
							help='Yaml output directory path, will use with conda-mirror' )
	
	parser.add_argument( '--show-command', dest='isOnlyShowCommand',
		     				action='store_true',
							help='Flag to show only command, it won\'t run conda command' )

	# parse args
	args = parser.parse_args()
	
	# get config path
	configJsonPath = args.packageConfigPath
	isOnlyShowCommand = args.isOnlyShowCommand
	yamlOutputDirectoryPath = args.yamlOutputDirectoryPath

	# open file json
	# construct package list to single line in format pkgName=version
	#	Example python=3.10.6 foo=1.0.0 bar=0.1.0
	with open( configJsonPath, 'r' ) as f:
		pkgConfigDict = json.load( f )

	print( f'Load config from: {configJsonPath}' )
	
	# initial package list
	# NOTE: just keep in mind, is it can load all package from single install command ? 
	# 		OR need to get a package one by one ?
	#		If found any issue about cannot place all package to a single command line, 
	#		please address and start to fix here
	pkgList = []

	# loop all pkg config data
	#	get key "name" and "version"
	#	if value in version is not found, get latest, leave it empty after pkgName
	for pkgConfigData in pkgConfigDict[ 'PackageInfo' ]:
		
		# if cannot get key, raise KeyError
		pkgName = pkgConfigData[ 'name' ]
		version = pkgConfigData[ 'version' ]

		# initial package data str with pkgName
		pkgData = f'{pkgName}'
		
		# check is valid, currently leave it should not empty
		if version:
			pkgData = f'{pkgData}={version}'
		
		pkgList.append( pkgData )

	# to show package
	for pkgData in pkgList:
		print( f'Package to mirror: {pkgData}' )

	# construct conda package to single line from pkgList 
	pkgListStr = ' '.join( pkgList )

	# construct command to install
	condaCommandStr = f'conda install --channel conda-forge --override-channel --json --dry-run {pkgListStr}'

	if isOnlyShowCommand:
		# print command
		print( f'run command: {condaCommandStr}' )
		return
	
	# run command to get package meta data in json format
	print( 'Get package meta data...' )
	condaProcess = subprocess.run( shlex.split( condaCommandStr ), stdout=subprocess.PIPE )
	condaPackageMetaDataStr = condaProcess.stdout.decode()
	condaPackageMetaData = json.loads( condaPackageMetaDataStr )

	########################################################################
	#
	# extract data from meta data
	# 

	# LINK is package that need to install. 
	# I'll follow LINK and trust that it's package that need to install
	packageDetailDict = condaPackageMetaData[ 'actions' ][ 'LINK' ]

	noArchList = []
	archList = []

	for package in packageDetailDict:
		
		# get platform
		platform = package[ 'platform' ]
		packageName = package[ 'name' ]
		version = package[ 'version' ]
		build = package[ 'build_string' ]
		dataDict = {
			'name' : packageName,
			'version' : version,
			'build' : build
		}

		if platform == 'noarch':
			noArchList.append( dataDict )
		else:
			archList.append( dataDict )

	noArchYamlPath = os.path.join( yamlOutputDirectoryPath, 'noarch.yaml' )
	noArchYamlPath = os.path.join( yamlOutputDirectoryPath, 'osx-arm64.yml' )

	saveFileYml( 'noarch.yml', noArchList )
	saveFileYml( 'osx-arm64.yml', archList )


########################################################
#
#	call main
#

if __name__=='__main__':
	main()

