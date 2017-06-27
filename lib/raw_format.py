#!/usr/bin/python2
# -*- coding: UTF-8 -*-

import commands
from subprocess import Popen,PIPE,call,STDOUT
import os, sys
import getopt
import parted
sys.path.append('/usr/lib/mintstick')
from mountutils import *
import syslog

def execute(command):
    syslog.syslog(str(command))
    call(command)
    call(["sync"])

def raw_format(device_path, fstype, volume_label, uid, gid):

    do_umount(device_path)

    partition_path = "%s1" % device_path
    if fstype == "fat32":
        partition_type = "fat32"
    if fstype == "ntfs":
        partition_type = "ntfs"
    elif fstype == "ext4":
        partition_type = "ext4"

    # First erase MBR and partition table , if any
    execute(["dd", "if=/dev/zero", "of=%s" % device_path, "bs=512", "count=1"])

    # Make the partition table
    execute(["parted", device_path, "mktable", "msdos"])

    # Make a partition (primary, with FS ID ext3, starting at 1MB & using 100% of space).
    # If it starts at 0% or 0MB, it's not aligned to MB's and complains
    execute(["parted", device_path, "mkpart", "primary", partition_type, "1", "100%"])

    # Call wipefs on the new partitions to avoid problems with old filesystem signatures
    execute(["wipefs", "-a", partition_path, "--force"])

    # Format the FS on the partition
    if fstype == "fat32":
        execute(["mkdosfs", "-F", "32", "-n", volume_label, partition_path])
    if fstype == "ntfs":
        execute(["mkntfs", "-f", "-L", volume_label, partition_path])
    elif fstype == "ext4":
        execute(["mkfs.ext4", "-E", "root_owner=%s:%s" % (uid, gid), "-L", volume_label, partition_path])

    # Exit
    sys.exit(0)

def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:f:l:u:g:", ["help", "device=","filesystem=","label=","uid=","gid="])
    except getopt.error, msg:
        print msg
        print "yardım için --help"
        sys.exit(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            print "Kullanımı: %s -d device -f filesystem -l volume_label\n"  % sys.argv[0]
            print "-d|--device          : aygıt yolu"
            print "-f|--filesystem      : filesystem\n"
            print "-l|--label           : bölüm etiketi\n"
            print "-u|--uid             : kullanıcı uid\n"
            print "-g|--gid             : kullanıcı gid\n"
            print "Örnek : %s -d /dev/sdj -f fat32 -l \"USB Bellek\" -u 1000 -g 1000" % sys.argv[0]
            sys.exit(0)
        elif o in ("-d"):
            device = a
        elif o in ("-f"):
            if a not in [ "fat32", "ntfs", "ext4" ]:
                print "fat32 belirle, ntfs veya ext4"
                sys.exit(3)
            fstype = a
        elif o in ("-l"):
            label = a
        elif o in ("-u"):
            uid = a
        elif o in ("-g"):
            gid = a

    argc = len(sys.argv)
    if argc < 11:
      print "Çok az argüman"
      print "yardım için --help"
      exit(2)

    raw_format(device, fstype, label, uid, gid)

if __name__ == "__main__":
    main()
