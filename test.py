import subprocess
import errno
import os

def pid_exists(pid):
    """Check whether pid exists in the current process table.
    UNIX only.
    """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True


backup_procs={}

if backup_proc == 0:
    proc = subprocess.Popen(['sleep','10'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    backup_proc=proc.pid
    while not proc.poll():
        
else
    print('backup already running')

proc = subprocess.Popen(['sleep','10'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
while not proc.poll():

    print(proc.pid)


print(proc.pid)
proc.poll()

>>> print(proc.pid)
279005
>>> proc.poll()
0
>>>



# try:
#     time.sleep(0.2)
#     resp = urllib.request.urlopen('http://localhost:8070')
#     assert b'Directory listing' in resp.read()
# finally:
#     proc.terminate()
#     try:
#         outs, _ = proc.communicate(timeout=0.2)
#         print('== subprocess exited with rc =', proc.returncode)
#         print(outs.decode('utf-8'))
#     except subprocess.TimeoutExpired:
#         print('subprocess did not terminate in time')