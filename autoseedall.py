#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# If you have question, contact me TG @CodyDoby

import os, re, sys, time, datetime
import subprocess, shlex
import math, random
import json

# reload(sys)
clear = lambda: os.system('cls' if os.name=='nt' else 'clear')

# Those info are get from *the* docker container (image)
# download_watch_path = '~/downloads'
download_watch_path = '/downloads'
# config_session_path = '~/config'
config_session_path = '/config'
chtor_cmd    = os.path.join(config_session_path, '.local/pyroscope/bin/chtor')
lstor_cmd    = os.path.join(config_session_path, '.local/pyroscope/bin/lstor')
rtxmlrpc_cmd = os.path.join(config_session_path, '.local/pyroscope/bin/rtxmlrpc')
session_path = os.path.join(config_session_path, 'rtorrent/rtorrent_sess')
download_path = os.path.join(download_watch_path)
watch_path_puppet = os.path.join(download_watch_path, "watch_puppet")

print('root_path: %s' % download_watch_path)
print('session_path: %s' % session_path)
print('download_path: %s' % download_path)

def execute(cmd):
    output = subprocess.check_output(cmd, shell=True)
    return output

# For convenience, our work path is switched here
os.chdir(session_path)

execute('mkdir -p %s' % os.path.join(session_path, 'log'))
log = open("%s" % os.path.join(session_path, 'log', 'log.txt'), 'a')

torrent_id = ''
name = ''

def write_log(s, log=log):
    print(log)
    timestamp = datetime.datetime.today().strftime('%Y%m%d_%H%M%S')
    log.write('%s ' % timestamp)
    log.write('%s: ' % torrent_id)
    log.write(s + '\n')
    log.flush()

def getidname():
    global torrent_id, name
    print("sys.argv len: %d" % len(sys.argv))
    write_log("sys.argv: {}".format(sys.argv))
    for i in range(len(sys.argv)):
        print('%d: %s' % (i, sys.argv[i]))
    name = sys.argv[1]
    torrent_id = sys.argv[2]
    write_log(torrent_id)
    write_log(name)
    print('Torrent name: %s' % name)
    return torrent_id, name


def get_info():
    ret = []
    files = execute("ls -1 | grep -E '\.torrent$'").strip().split('\n')
    for file in files:
        # name = execute("%s %s | grep -E ^Name:" % (transmission_show_cmd, file)).strip()[6:]
        name = execute("%s -o info.name %s" % (lstor_cmd, file)).split('\n')[0]
        write_log(name)
        hx = file.strip().split('.')[0]
        ret.append((name, hx))
    return ret


def add_recovery(torrent_id, torrent_folder):
    write_log('%s add_recovery...'%torrent_id)
    path = os.path.join(download_path, torrent_folder)
    cmd = '%s %s.torrent --hashed=\'%s\'' % (chtor_cmd, torrent_id, path)
    print(cmd)
    r = execute(cmd)
    write_log(r)
    write_log('Success')

def getidbyname(name, torrents_info):
    write_log('getidbyname... %s'%name)
    ret = []
    for nm, hx in torrents_info:
        if name == nm:
            ret.append(hx)
    return ret

def re_add_start(torrent_id):
    write_log('%s re_add_start...'%torrent_id)
    torrent_path = os.path.join(session_path, '%s.torrent'%torrent_id)
    cmd = 'cp %s %s'% (torrent_path, watch_path_puppet)
    write_log(execute(cmd))
    write_log('Success')

def check_statue(torrent_id):
    write_log('check status for %s...'%torrent_id)
    cmd = '%s d.connection_current %s' % (rtxmlrpc_cmd, torrent_id)
    ret = execute(cmd).strip()
    write_log('finished, %s' % ret)
    return ret

def main():
    write_log('Running start...')
    write_log('Current path: %s' % os.path.abspath('.'))
    finid, name = getidname()
    torrents_info = get_info()
    write_log('Found %d torrents in your session.' % len(torrents_info))

    if (name, finid.upper()) not in torrents_info:
        write_log('Not find this torrent. Added forcibly.')
        torrents_info.append((name, finid.upper()))
    else:
        write_log('Already found this torrent in session.')

    l = getidbyname(name, torrents_info)
    write_log(str(l))
    if len(l) <= 1:
        write_log('No other same name torrent. Exit. (%d)' % len(l))
        return
    else:
        write_log('Found %d same name torrent. ' % len(l))
        hash_status = [(i, check_statue(i)) for i in l]
        write_log('hash status: {}'.format(hash_status))
        if 'seed' not in [j for i,j in hash_status]:
            print('All torrents in leetch status, exit.')
            return
        for hx, status in hash_status:
            if 'seed' not in status:
                write_log('Start torrent %s'%hx)
                add_recovery(hx, name)
                re_add_start(hx)

    write_log('Running finished.')

if __name__ == '__main__':
    main()
