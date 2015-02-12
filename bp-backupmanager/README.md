Backup Manager Backend
===============

Hard drive backups making use of Hard Links to mitigate space

## Functionality

This is a primitive backup system that makes use of hard links and rsync to backup files.  It has the ability to do primitive deduping on a day-to-day basis.  You can pull from CIFS or Linux machines (via SSH/RSYNC).  

This system is good for:

* File level backups

This system is NOT for:

* Backups that need ACL level backups
* Many files that are held open (Database files)

## How It Works

Backups are stored on the local disk of the machine.  Each day a backup is run and compared against the previous backup.  If a difference is detected a new copy is made.  If the file is the same as the previous backup the file is hard linked to the previous inode saving space.

## Installation

This repo is meant to be built into a deb package for debian.  The installation and this section need some polish
