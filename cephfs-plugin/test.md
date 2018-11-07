Tests
=====

- ![#008000](https://placehold.it/15/008000/000000?text=+) 
  Installation
  ```console 
    $ docker plugin install heliumdatacommons/cephfs CEPH_MON_HOST=10.52.100.3
    Plugin "heliumdatacommons/cephfs" is requesting the following privileges:
     - network: [host]
     - capabilities: [CAP_SYS_ADMIN]
    Do you grant the above permissions? [y/N] y
    latest: Pulling from heliumdatacommons/cephfs
    e296bfa5386a: Download complete 
    Digest: sha256:af603607062228e3f199cff6af14bd4056e22f74bfb634ec6a0c6e89cd78f32b
    Status: Downloaded newer image for heliumdatacommons/cephfs:latest
    Installed plugin heliumdatacommons/cephfs
  ```
- ![#008000](https://placehold.it/15/008000/000000?text=+)
  Create a volume
  ```console
   $ docker volume create -d heliumdatacommons/cephfs alpha
   alpha
  ```
- ![#008000](https://placehold.it/15/008000/000000?text=+)
  List volumes
  ```console
    $ docker volume ls
    DRIVER                            VOLUME NAME
    heliumdatacommons/cephfs:latest   alpha
  ```
- ![#008000](https://placehold.it/15/008000/000000?text=+)
  Mount an existing volume to a container
  ```console
    $ docker run -it -v alpha:/tmp ubuntu /bin/bash
    root@e9cac6dab7f8:/# df -h
    Filesystem      Size  Used Avail Use% Mounted on
    overlay          29G   20G  9.5G  68% /
    tmpfs            64M     0   64M   0% /dev
    tmpfs           3.7G     0  3.7G   0% /sys/fs/cgroup
    10.52.100.3:/    93G     0   93G   0% /tmp 
  ```
- ![#008000](https://placehold.it/15/008000/000000?text=+)
  Unmount a volume from a container 
  ```console 
  root@e9cac6dab7f8:/# exit
  $ mount | grep ceph
  ```
- ![#008000](https://placehold.it/15/008000/000000?text=+) 
  Remove a volume 
  ```console
  $ docker volume rm -f alpha 
  alpha
  ```
- ![#008000](https://placehold.it/15/008000/000000?text=+) 
  Create and mount a volume to a container using `docker run`
  ```console
    $ docker run -it \
    >     --volume-driver=heliumdatacommons/cephfs \
    >     -v alpha:/tmp ubuntu /bin/bash 
    root@43ad0ebf11d1:/# df -h
    Filesystem      Size  Used Avail Use% Mounted on
    overlay          29G   20G  9.5G  68% /
    tmpfs            64M     0   64M   0% /dev
    tmpfs           3.7G     0  3.7G   0% /sys/fs/cgroup
    10.52.100.3:/    93G     0   93G   0% /tmp
  ```
- ![#f03c15](https://placehold.it/15/f03c15/000000?text=+) 
  Create and mount a volume to two containers simultaneously
  ```console 
    $ docker run -d --name cephfs-1 \
    >     --volume-driver=heliumdatacommons/cephfs -v alpha:/tmp ubuntu tail -f /dev/null &
    [1] 15702
    centos@benchmark-us-east1-b-cephfs-1:~$     docker run -d --name cephfs-2 \
    >     --volume-driver=heliumdatacommons/cephfs -v alpha:/tmp ubuntu tail -f /dev/null &
    [2] 15959
    docker: Error response from daemon: VolumeDriver.Mount: mount: mounting 10.52.100.3:/ on /mnt/cephfs/alpha failed: Resource busy.
    See 'docker run --help'.
    1b3df27b34ce72c6b154bc628d329c7eb978e7f674a8114b13b9a564675f911e
    
    [1]-  Done                    docker run -d --name cephfs-1 --volume-driver=heliumdatacommons/cephfs -v alpha:/tmp ubuntu tail -f /dev/null
    [2]+  Exit 125                docker run -d --name cephfs-2 --volume-driver=heliumdatacommons/cephfs -v alpha:/tmp ubuntu tail -f /dev/null
  ```
  **Note:** it occasionally occurs since both containers contend on mounting the newly created volume 
  to the same mountpoint and cause the `Resource Busy` error. Lock needs to be added to protect the
  volume mount. 
- ![#008000](https://placehold.it/15/008000/000000?text=+) 
  List a volume created on another host 
  ```console
    # host 1
    $ docker volume ls
    DRIVER              VOLUME NAME
    $ docker volume create -d heliumdatacommons/cephfs alpha
    alpha
    $ docker volume ls
    DRIVER                            VOLUME NAME
    heliumdatacommons/cephfs:latest   alpha
    
    # host 2
    
    # before volume creation
    $ docker volume ls
    DRIVER              VOLUME NAME
    
    # after volume creation
    $ docker volume ls
    DRIVER                            VOLUME NAME
    heliumdatacommons/cephfs:latest   alpha
  ```
- ![#bbbbbb](https://placehold.it/15/bbbbbb/000000?text=+)
  Create multiple volumes 