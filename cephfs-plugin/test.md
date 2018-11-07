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
- ![#008000](https://placehold.it/15/008000/000000?text=+)
  Create and mount a volume to multiple containers simultaneously
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
  **Note:** It occasionally occurs since both containers contend on mounting the newly created volume 
  to the same mountpoint and cause the `Resource Busy` error. Lock needs to be added to protect the
  volume mount.
  
  **Solution:** [Resolved by adding lock on volume mount to avoid race](https://github.com/heliumdatacommons/pivot-data/blob/c63df998ad5f913061fd2ad7bde57de06eb10f27/cephfs-plugin/src/ceph.py#L60-L64) 
  
- ![#008000](https://placehold.it/15/008000/000000?text=+)
  Mount an existing volume to multiple containers simultaneously
  ```console 
    $ for j in `seq 10`;do
    >   docker run -d --name cephfs-${j} --rm --volume-driver=heliumdatacommons/cephfs -v alpha:/tmp ubuntu tail -f /dev/null &
    > done
    b8456ed0dcad682d73771dfa199d122bfa580dd3e92b3e788351644e54ae6b4f                                                                                                                                   
    a66c7f0a69426c9fe0b94e00fbb2bd370501ec5257d4ab1d84601ff9a8076465                                                                                                                                                                           
    42be6ad53b07913e13a861613f7c91aaf1ac11fffc0c04b994074b2da60687aa                                                                                                                                                                            
    e29bdaf41e8db2f4aaf84902c4a65c17afd6c8ba82050aa044558e71049c3ad7                                                                                                                                                                           
    c0ca6139ab51104e8b3826fbdfe8375dc8ab3d4c47ab05e4cf2b04045d5f37e8                                                                                                                                                                           
    a9323557b714e6abe7af5209cae57f3544d095907628d9d4c69c24e950aa7dd4                                                                                                                                                                           
    f67efa044a7dd138e7ec074d1d189b110def79438d0d2792bf45e02e8dd46d24                                                                                                                                                                           
    542da807c9eaec74d5949ccb75f7aea5fc1defe0f47ae89b1fed237dcabbc9c2                                                                                                                                                                           
    d00724402e4d857df640cbcd43bd877eed3c32084c6a506ebac0ad1ec9ed9c1c                                                                                                                                                                           
    011825169bfc8d6e9b64efbff4eb848d2235bc0a83fa4a066ccfd665bf61810c                                                                                                                                                                           
    docker: Error response from daemon: OCI runtime create failed: container_linux.go:348: starting container process caused "process_linux.go:402: container init caused \"rootfs_linux.go:58: mounting \\\"/var/lib/docker/plugins/889b2fb60b9
    9773c5c328dbc976b98594f918bff2899fc39f9671982cfa30d1f/propagated-mount/alpha\\\" to rootfs \\\"/var/lib/docker/overlay2/cf037cd199116309f0671413037621e101c03659dcb8eb78e37294be64e40232/merged\\\" at \\\"/tmp\\\" caused \\\"stat /var/lib
    /docker/plugins/889b2fb60b99773c5c328dbc976b98594f918bff2899fc39f9671982cfa30d1f/propagated-mount/alpha: no such file or directory\\\"\"": unknown.                                                                                        
    docker: Error response from daemon: OCI runtime create failed: container_linux.go:348: starting container process caused "process_linux.go:402: container init caused \"rootfs_linux.go:58: mounting \\\"/var/lib/docker/plugins/889b2fb60b9
    9773c5c328dbc976b98594f918bff2899fc39f9671982cfa30d1f/propagated-mount/alpha\\\" to rootfs \\\"/var/lib/docker/overlay2/858e629d52694e806f8ae5bfdf17eaff04c5b4ea48f1042173877c88656023ed/merged\\\" at \\\"/tmp\\\" caused \\\"stat /var/lib
    /docker/plugins/889b2fb60b99773c5c328dbc976b98594f918bff2899fc39f9671982cfa30d1f/propagated-mount/alpha: no such file or directory\\\"\"": unknown.                                                                                         
    docker: Error response from daemon: OCI runtime create failed: container_linux.go:348: starting container process caused "process_linux.go:402: container init caused \"rootfs_linux.go:58: mounting \\\"/var/lib/docker/plugins/889b2fb60b9
    9773c5c328dbc976b98594f918bff2899fc39f9671982cfa30d1f/propagated-mount/alpha\\\" to rootfs \\\"/var/lib/docker/overlay2/38857a5cbdf90b7dc85ddb36f905defc9c53875d827ac419da934b22b299e9da/merged\\\" at \\\"/tmp\\\" caused \\\"stat /var/lib
    /docker/plugins/889b2fb60b99773c5c328dbc976b98594f918bff2899fc39f9671982cfa30d1f/propagated-mount/alpha: no such file or directory\\\"\"": unknown.
  ```
  
  **Note:** It is probably caused by the unnecessary mountpoint deletion performed during volume 
  unmount. Since every CephFS volume has a dedicated mountpoint shared among all the containers 
  mounted to the volume, deleting the mountpoint directory could make the mountpoint invisible to 
  other containers in the process of volume mount and thus fails the mounts. Since Docker performs 
  the volume unmount asynchronously in the background, the unmount operations for previous containers
  could affect subsequently created ones and lead to the error.
  
  **Solution:** Removed mountpoint deletion during the volume unmount but performed it during volume
  deletion instead. 
   
  
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