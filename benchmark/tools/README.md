Benchmark Tools
===============
We use [smallfile](https://github.com/distributed-system-analysis/smallfile), 
[fio](http://freshmeat.sourceforge.net/projects/fio) and [iozone](http://www.iozone.org/) as 
the tools for testing the distributed file systems, since they have certain advantages specifically 
for testing distributed file systems as recognized in this 
[post](https://gluster.readthedocs.io/en/latest/Administrator%20Guide/Performance%20Testing/).

The tools are containerized to emulate the working environment of real workloads. Besides, it also 
facilitates the portability of the tools. 

### Pre-requisite

- Docker must be installed 
- The kernel module(s) for the target filesystem (if any) must be loaded
- The container must run with `--privileged` in order to access system resources   

### Build Docker image

The `./build.sh` is used for building the docker image and pushing it to Docker Hub under the 
`dchampion24` namespace. The usage is as
below:

```bash
$ ./build.sh <build|push|build-and-push(default)> <tool(default: iozone)> 
```

### Container usage

The tool container reads the following parameters from the environment variables.
```
FS_TYPE     Filesystem type (*e.g.*, nfs, ceph, glusterfs)
FS_HOST     The hostname/IP address of the target filesystem endpoint 
FS_DIR      The exported directory on the target filesystem (default: /)
FS_OPTS     The mount options (optional)
MOUNTPOINT  The mount point (default: /mnt) 
```

The target file system will be mounted to the `MOUNTPOINT`, and the container will then use it as 
the working directory. 
 
