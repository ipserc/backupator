#! /usr/bin/python3
# encoding: utf-8
'''
backupator makes folders and files copies from origin to destination  

backupator makes folders and files (fobjects from now on) copies from origin to destination.
It only copies fobjects if they don't exsit. In case the files exist they are updated if the same files have different md5sum 
The program can be launched with the forced option (-f) to force the copy of the origin file to the destination

It defines classes_and_methods

@author:     Jose Luis Núñez

@copyright:  2025 Ipserc. All rights reserved.

@license:    MIT

@contact:    joseluis.nunez@selenitas.es
@deffield    updated: need2update comapres with (args['date'] and fwkTime > prjTime) or (fwkmd5 != prjmd5)
'''
import os
import sys
import shutil
import hashlib
import time
import datetime
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from pathlib import Path

__VERBOSE__ = False
__TEST_MODE__ = False


# #########################
# PROGRAM FACTS
# #########################
__PROGRAM_NAME__ = sys.argv[0]
__AUTHOR__ = "Ipserc"
__CREATION_DATE__ = "2025/02/22"
__UPDATE_DATE__ = "2025/02/22"
__VERSION__ = "1.0 (2025_0222_1113)"


# #################################################
# Function: printFacts():
# Imprime los datos del programa.
# #################################################
def printFacts():
	print("********************** PROGRAM FACTS **********************")
	print("Program..........:", __PROGRAM_NAME__)
	print("Version..........:", __VERSION__)
	print("Author...........:", __AUTHOR__)
	print("Update Date......:", __UPDATE_DATE__)
	print("***********************************************************")
	print()
	
# #################################################
# class CLIError(Exception):
# @param: Exception
# #################################################
class CLIError(Exception):
	'''Generic exception to raise and log different fatal errors.'''
	def __init__(self, msg):
		super(CLIError).__init__(type(self))
		self.msg = "Exception: %s" % msg
		print(self.msg)
	def __str__(self):
		return self.msg
	def __unicode__(self):
		return self.msg

# #################################################
# Function: parseArgs(argv=None)
# @param: argv
# Parsea los parámetros que se le pasan al programa 
# y chequea su validez.
# Presenta la descripción del programa y sus parámetros
# admitidos.
# indica cómo se tiene que invocar el programa.
# #################################################
def parseArgs(argv=None): 
	'''Command line options.'''

	if argv is None:
		argv = sys.argv
	else:
		sys.argv.extend(argv)

	program_name = os.path.basename(sys.argv[0])
	program_version = "v%s" % __VERSION__
	program_build_date = str(__UPDATE_DATE__)
	program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
	program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
	program_license = '''
  Version of %s
	
  %s
  
  Created by Jose Luis Nuñez Crespi in %s.
  Copyright 2020 organization_name. All rights reserved.

  Licensed under the MIT License
  https://opensource.org/license/mit

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.
  
  USAGE
''' % (program_version_message, program_shortdesc, str(__CREATION_DATE__))

	try:
		# Setup argument parser
		parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
		parser.add_argument("-s", "--sourceDir", dest="sourceDir", help="Source directory path to backup")
		parser.add_argument("-d", "--destinationDir", dest="destinationDir", help="Destination directory path (without the folder subject of the backup)")
		parser.add_argument("-f", "--force", dest="force", action='store_true', default=False, help="Forces copy of same files to destination [default: %(default)s]")
		parser.add_argument("-t", "--testMode", dest="testMode", action='store_true', default=False, help="Activates test mode, none folder/file is copied [default: %(default)s]")
		parser.add_argument("-v", "--verbose", dest="verbose", action='store_true', default=False, help="Sets verbosity to true [default: %(default)s]")
		parser.add_argument('-V', '--version', action='version', version=program_version_message)

		# Process arguments
		args = parser.parse_args()

		copiaTotal = False
		sourceDir = args.sourceDir
		destinationDir = args.destinationDir

		if args.testMode == True:
			print("Test Mode ON: none copy or update will be done")

		if args.verbose == True:
			print("Verbose Mode ON: all the folders and files will be displayed")

		if args.force == True:
			print("Using force: Origin files will be copied to destination always")

		if sourceDir == None:
			raise CLIError("Source Directory is required")
		
		if not os.path.exists(sourceDir):
			raise CLIError("ERROR Invalid Source Path")

		if destinationDir == None:
			raise CLIError("Destination Directory is required")
		
		if not os.path.exists(destinationDir) :
			copiaTotal = True

		return {'sourceDir':sourceDir, 'destinationDir':destinationDir, 'force':args.force, 'testMode':args.testMode, 'verbose':args.verbose, 'copiaTotal':copiaTotal}
	   
	except Exception:
		indent = len(program_name) * " "
		sys.stderr.write(program_name + ": " + repr(Exception) + "\n")
		sys.stderr.write(indent + "  for help use --help")
		raise(Exception)

# #################################################
# Function: traza(cadena)
# @param: cadena
# Imprime por pantalla una traza con el mensaje que 
# se le pasa en cadena.
# La traza solo se imprime si el modo verbose está
# activado.
# #################################################
def traza(cadena):
	if __VERBOSE__: print(cadena)

# #################################################
# Function: time_ns_to_datetime(timeNs)
# @param: timeNS
# @return: datetime en formato '%Y-%m-%d %H:%M:%S,%f'
# Convierte un valor time_ns en una cadena de texto
# que representa un datetime en formato '%Y-%m-%d %H:%M:%S,%f'.
# #################################################
def time_ns_to_datetime(timeNs):
	return datetime.datetime.fromtimestamp(timeNs/1.0E9).strftime('%Y-%m-%d %H:%M:%S,%f')

# #################################################
# Function: time_ns_to_time(timeNs)
# @param: timeNS
# @return: datetime en formato '%H:%M:%S,%f'
# Convierte un valor time_ns en una cadena de texto
# que representa un datetime en formato '%H:%M:%S,%f'.
# Se requiere el timezone.utc para que la representación
# de la hora no esté afectada por la zona temporal local.
# #################################################
def time_ns_to_time(timeNs):
	return datetime.datetime.fromtimestamp(timeNs/1.0E9, tz=datetime.timezone.utc).strftime('%H:%M:%S,%f')

# #################################################
# Function: md5(fname):
# @param: fname ruta a un archivo 
# @return: El hash md5
# Calcula el hash md5 de un determinado archivo.
# #################################################
def md5(fname):
	hash_md5 = hashlib.md5()
	with open(fname, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)
	return hash_md5.hexdigest()

# #################################################
# Function: backupFiles(sourceFileNames, sourceDirPath, destinationDirPath, force):
# @param: sourceFileNames Lista con los archivos encontrados en sourceDirPath
# @param: sourceDirPath La ruta al directorio que contiene los archivos fuente
# @param: destinationDirPath La ruta al directorio en el que se hará el backup de los archivos
# @param: force Flag que indica si el backup es forzado. Los archivos se copiarán aunque fuente y destino sean iguales
# Realiza el backup de los archivos que envuantra en el directorio fuento y los deposita en el directorio destino
# El backup se realiza de vairas formas:
# 1. Si el archivo origen no está en el destino se copia.
# 2. Si el archivo origen está en el destino se calcula el hash md5 de ambos.
# 2.1. Si el hash coincide se salta.
# 2.2. Si el hash es diferente se actualiza el archivo destino con el archivo fuente.
# En el modo force (True) el archivo se destino se actualiza independientemenet del hash que tenga.
# #################################################
def backupFiles(sourceFileNames, sourceDirPath, destinationDirPath, force):
	traza("***** sourceDirPath:" + sourceDirPath)
	traza("***** destinationDirPath:" + destinationDirPath)
	for filename in sourceFileNames:
		doCopyFlag = False
		sourceFileName = os.path.join(sourceDirPath,filename)
		destFilename = os.path.join(destinationDirPath,filename)
		if (not force):
			if (os.path.exists(destFilename)):
				md5Source = md5(sourceFileName)
				md5Dest = md5(destFilename)
				if (md5Source != md5Dest):
					print("Updating %s into %s" % (filename, destinationDirPath))
					doCopyFlag = True
				else:
					traza("Skiping copy of %s into %s" % (filename, destinationDirPath))
			else:
				print("Copying %s into %s" % (filename, destinationDirPath))
				doCopyFlag = True
		else:
			print("Copying FORCE %s into %s" % (filename, destinationDirPath))
			doCopyFlag = True
		if (doCopyFlag and not __TEST_MODE__):
			shutil.copy(sourceFileName, destFilename)

# #################################################
# Function: backupDir(destinationDir):
# @param: destinationDir - Directorio destino
# Comprueba si existe el directorio destino. 
# Este directorio se corresponde con el directorio fuente donde se depositaran los archivos de backup.
# Si el directorio destino no existe lo crea. 
# Esta función crea una réplica de la estuctura de directorios de la fuente.
# #################################################
def backupDir(destinationDir):
	if (not os.path.exists(destinationDir)):
		print("Creating " + destinationDir)
		if not __TEST_MODE__: os.makedirs(destinationDir)
	else:
		traza("Skiping creation of:" + destinationDir)

# #################################################
# Function: doBackUp(sourceDir, destinationDir, force):
# @param: sourceDir - La ruta del directorio fuente que contiene los archivos
# @param: destinationDir - La ruta del directorio destino donde se van a guarda los archivos fuentes
# @param: force - Flag que indica si el backup de archivos va a ser forzado
# Esta función se llama de forma recursiva para recorrer las ramas del arbol de directorios de la fuente.
# Desde la raiz y por cada rama, recupera la lista de archivos que contiene la fuente  y hace el backup 
# en la ruta equivalente destino.
# Esa lista de archivos se procesa con backupFiles.
# Por cada rama fuente, llama a backupDir uqe comprueba si existe en el destino, y si no la crea.
# #################################################
def doBackUp(sourceDir, destinationDir, force):
	#recorrer los archivos del framework
	(sourceDirPath, sourceDirNames, sourceFileNames) = next(os.walk(sourceDir), ([],[],[]))
	#Check files
	backupFiles(sourceFileNames, sourceDirPath, destinationDir, force)
	#Check Sub Dirs
	for subDir in sourceDirNames:
		backupDir(os.path.join(destinationDir, subDir))
		doBackUp(os.path.join(sourceDirPath, subDir), os.path.join(destinationDir, subDir), force)

# #################################################
# Function: doTotalCopy(sourceDir, destinationDir):
# @param: sourceDir - La ruta del directorio fuente que contiene los archivos
# @param: destinationDir - La ruta del directorio destino donde se van a guarda los archivos fuentes
# En el caso en el que la carpeta que contiene los archivos fuente no se encuentre en el destino 
# se realiza una réplica de la carpeta fuente en la ruta destino.
# #################################################
def doTotalCopy(sourceDir, destinationDir):
	# Preguntar si se está seguro de hacer una copia total
	print("************************ TOTAL COPY ***********************")
	print("A complete copy from %s is about to be done in %s" % (sourceDir, destinationDir))
	reply = input(">>>> Enter 'Y' to continue:")
	if (reply.upper() == "Y"):
		backupInitTime = time.time_ns()
		print("Total copy/Initial copy started at %s" % (time_ns_to_datetime(backupInitTime)))
		if not __TEST_MODE__: shutil.copytree(sourceDir, destinationDir)
		backupEndTime = time.time_ns()
		print("Total copy/Initial copy finished at %s" % (time_ns_to_datetime(backupEndTime)))
		print("Total copy/Initial copy duration %s" % (time_ns_to_time(backupEndTime-backupInitTime)))
	else:
		print("Total copy/Initial copy aborted")
	
# #################################################
#
# MAIN PROGRAM
#
# #################################################
if __name__ == '__main__':
	printFacts()
	args = parseArgs()

	if (not os.path.isdir(args['sourceDir'])):
		print("ERROR: Source is not a directory.")
		os._exit(101)

	if (not os.path.isdir(args['destinationDir'])):
		print("ERROR: Destination is not a directory.")
		os._exit(102)

	sourceDir = args['sourceDir']
	targetFolder = Path(sourceDir).parts[-1]
	destinationDir = os.path.join(args['destinationDir'], targetFolder)
	__VERBOSE__ = args['verbose']
	__TEST_MODE__ = args['testMode']
	
	if (sourceDir == destinationDir):
		print("ERROR: Source and destination directories are the same. This is not allowed.")
		os._exit(100)

	if (os.path.exists(destinationDir)):
		print("************************** BACKUP *************************")
		print("Backup of %s" % (targetFolder))
		print("	from Source...: %s" % (sourceDir))
		print("	to Destination: %s"  % (destinationDir))
		reply = input(">>>> Enter 'Y' to continue:")
		if (reply.upper() == "Y"):
			backupInitTime = time.time_ns()
			print("Backup started at %s" % (time_ns_to_datetime(backupInitTime)))
			doBackUp(sourceDir, destinationDir, args['force'])
			backupEndTime = time.time_ns()
			print("Backup finished at %s" % (time_ns_to_datetime(backupEndTime)))
			print("Backup duration %s" % (time_ns_to_time(backupEndTime-backupInitTime)))
		else:
			print("Backup aborted")

	else:
		doTotalCopy(sourceDir, destinationDir)
	
	
