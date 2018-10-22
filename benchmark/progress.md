Progress
=================

#### 10/22/18

- [x] Create disks for the hosts
- [x] Create container for `iozone`
- [x] Create a test case for the existing *CephFS*
    - Tested on a `n1-standard-2` node on GCP backed with 3 HDD OSDs, and compared to *Overlay2* 
    and *PD SSD*. The experiments were run to verify if the `iozone` container is working as 
    expected and find out the possibility for the client-side design of the benchmark framework.  
    The results are far from representative due to the very limited node capacity and suboptimal 
    cluster configurations. 
      - CephFS
        ```bash 
        $ docker run -ti --rm --privileged \
            -e FS_TYPE=ceph \
            -e FS_HOST=10.52.100.3 \
            -e FS_DIR=/ \
            -e FS_OPTS=mds_namespace=beta \
            dchampion24/iozone \
            iozone -i 0 -i 1 -t 1 
        ``` 
        ```console 
        Children see throughput for  1 initial writers  =   79293.24 kB/sec
        Parent sees throughput for  1 initial writers   =   19238.75 kB/sec
        Min throughput per process                      =   79293.24 kB/sec 
        Max throughput per process                      =   79293.24 kB/sec
        Avg throughput per process                      =   79293.24 kB/sec
        Min xfer                                        =     512.00 kB

        Children see throughput for  1 rewriters        = 1120345.00 kB/sec
        Parent sees throughput for  1 rewriters         =   24724.98 kB/sec
        Min throughput per process                      = 1120345.00 kB/sec 
        Max throughput per process                      = 1120345.00 kB/sec
        Avg throughput per process                      = 1120345.00 kB/sec
        Min xfer                                        =     512.00 kB

        Children see throughput for  1 readers          = 2402629.00 kB/sec
        Parent sees throughput for  1 readers           =  613776.20 kB/sec
        Min throughput per process                      = 2402629.00 kB/sec 
        Max throughput per process                      = 2402629.00 kB/sec
        Avg throughput per process                      = 2402629.00 kB/sec
        Min xfer                                        =     512.00 kB

        Children see throughput for 1 re-readers        = 1541840.12 kB/sec
        Parent sees throughput for 1 re-readers         =  505432.30 kB/sec
        Min throughput per process                      = 1541840.12 kB/sec 
        Max throughput per process                      = 1541840.12 kB/sec
        Avg throughput per process                      = 1541840.12 kB/sec
        Min xfer                                        =     512.00 kB
        ```
      - Overlay2 
        ```bash 
        $ docker run -ti --privileged dchampion24/iozone \
        iozone -i 0 -i 1 -t 1 
        ```
        ```console
        Children see throughput for  1 initial writers  = 1139970.88 kB/sec
        Parent sees throughput for  1 initial writers   =   97432.18 kB/sec
        Min throughput per process                      = 1139970.88 kB/sec 
        Max throughput per process                      = 1139970.88 kB/sec
        Avg throughput per process                      = 1139970.88 kB/sec
        Min xfer                                        =     512.00 kB

        Children see throughput for  1 rewriters        = 1227971.62 kB/sec
        Parent sees throughput for  1 rewriters         =   72501.61 kB/sec
        Min throughput per process                      = 1227971.62 kB/sec 
        Max throughput per process                      = 1227971.62 kB/sec
        Avg throughput per process                      = 1227971.62 kB/sec
        Min xfer                                        =     512.00 kB

        Children see throughput for  1 readers          = 2360376.00 kB/sec
        Parent sees throughput for  1 readers           =  190484.36 kB/sec
        Min throughput per process                      = 2360376.00 kB/sec 
        Max throughput per process                      = 2360376.00 kB/sec
        Avg throughput per process                      = 2360376.00 kB/sec
        Min xfer                                        =     512.00 kB

        Children see throughput for 1 re-readers        = 2178404.50 kB/sec
        Parent sees throughput for 1 re-readers         =  424504.08 kB/sec
        Min throughput per process                      = 2178404.50 kB/sec 
        Max throughput per process                      = 2178404.50 kB/sec
        Avg throughput per process                      = 2178404.50 kB/sec
        Min xfer                                        =     512.00 kB
        ```
      - PD SSD
      ```bash
      docker run -ti --privileged -v /tmp/:/mnt dchampion24/iozone \
      iozone -i 0 -i 1 -t 1  
      ```
      ```console
        Children see throughput for  1 initial writers  =  974885.69 kB/sec
        Parent sees throughput for  1 initial writers   =   68706.71 kB/sec
        Min throughput per process                      =  974885.69 kB/sec 
        Max throughput per process                      =  974885.69 kB/sec
        Avg throughput per process                      =  974885.69 kB/sec
        Min xfer                                        =     512.00 kB

        Children see throughput for  1 rewriters        = 1368865.25 kB/sec
        Parent sees throughput for  1 rewriters         =   45450.54 kB/sec
        Min throughput per process                      = 1368865.25 kB/sec 
        Max throughput per process                      = 1368865.25 kB/sec
        Avg throughput per process                      = 1368865.25 kB/sec
        Min xfer                                        =     512.00 kB

        Children see throughput for  1 readers          = 2424328.00 kB/sec
        Parent sees throughput for  1 readers           =  121962.03 kB/sec
        Min throughput per process                      = 2424328.00 kB/sec 
        Max throughput per process                      = 2424328.00 kB/sec
        Avg throughput per process                      = 2424328.00 kB/sec
        Min xfer                                        =     512.00 kB

        Children see throughput for 1 re-readers        = 1992459.00 kB/sec
        Parent sees throughput for 1 re-readers         =  421091.27 kB/sec
        Min throughput per process                      = 1992459.00 kB/sec 
        Max throughput per process                      = 1992459.00 kB/sec
        Avg throughput per process                      = 1992459.00 kB/sec
        Min xfer                                        =     512.00 kB
      ```
        
        

