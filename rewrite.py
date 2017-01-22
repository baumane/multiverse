#!/usr/bin/python
import sys,os
import subprocess
import shutil

import renabler

def extract_libraries(fname):
  result = subprocess.check_output('ldd %s'%sys.argv[1], shell=True)
  libs = result.split('\n')
  paths = []
  for lib in libs:
    if '=>' in lib:
      path = lib[lib.find('=>')+2:lib.find(' (0x')].strip()
      if path != '':
        paths.append(path)
  return paths

def extract_dynamic_libraries(fname, libpath):
  paths = []
  dynlib = os.path.join(libpath, fname+'-dynamic-libs.txt')
  if os.path.exists(dynlib):
    with open(dynlib) as f:
      path = f.readline()
      while path != '':
        paths.append(path.strip())
        path = f.readline()
  return paths

def rewrite_libraries(libpath,paths):
  renabler.write_so = True
  for path in paths:
    (base,fname) = os.path.split(path)
    libname = os.path.join(libpath,fname)
    shutil.copy(path,libname)
    renabler.renable(libname)
    os.remove(libname)
    shutil.move(libname+'-r',libname)
    shutil.move(libname+'-r-map.json',libname+'-map.json')
    shutil.move(libname+'-r-stat.json',libname+'-stat.json')

if __name__ == '__main__':
  if len(sys.argv) == 2 or len(sys.argv) == 3:
    fpath = ''
    dynamic_only = False
    if len(sys.argv) == 2:
      fpath = sys.argv[1]
    else:
      fpath = sys.argv[2]
      if sys.argv[1] == '-d':
        dynamic_only = True
    
    paths = []
    
    if not dynamic_only:
      print 'Getting required libraries for %s'%fpath
      paths = extract_libraries(fpath)
    
    (base,fname) = os.path.split(fpath)
    libpath = os.path.join(base,fname+'-libs-r')
    if not os.path.exists(libpath):
      os.makedirs(libpath)
    print 'Getting dynamic libraries'
    paths.extend(extract_dynamic_libraries(fname,libpath))
    print 'Rewriting libraries'
    rewrite_libraries(libpath,paths)
    
    if not dynamic_only:
      print 'Rewriting main binary'
      renabler.write_so = False
      renabler.renable(fpath)
    
    print 'Writing runnable .sh'
    with open(fpath+'-r.sh', 'w') as f:
      ld_preload = ''
      for path in extract_dynamic_libraries(fname,libpath):
        (lbase,lname) = os.path.split(path)
        ld_preload += os.path.join(libpath,lname) + ' '
      f.write('#!/bin/bash\nLD_LIBRARY_PATH=./%s LD_BIND_NOW=1 LD_PRELOAD="%s" ./%s'%( fname+'-libs-r', ld_preload, fname+'-r' ) )
  else:
    print "Error: must pass executable filename.\nCorrect usage: %s <filename>"%sys.argv[0]