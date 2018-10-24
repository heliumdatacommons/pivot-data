Shared Filesystem Benchmark
===========================
Shared filesystem is commonly used among distributed containers to share data and states. 

The benchmark aims at testing various shared filesystem solutions for (geo-)distributed containers 
and finding the best one in terms of *read/write throughput*, *responsiveness* and *scalability*. 


### Usage pattern

The usage pattern of the shared filesystem by distributed containers are characterized as follows:

- Must be POSIX-compliant
- Frequent small random reads/writes, usually more reads than writes 
- Occasional bulk data transfers typically at the scale ranging from ~10 to ~1000 of GBs
- Concurrent reads/writes by multiple clients. The concurrency ranges from 2-3 to ~100.

### Performance definition and metrics

Based on the scenario and usage pattern, we define the performance metrics for evaluating a 
solution. In general, we evaluate the following aspects of every solution.

#### Throughput

We measure throughput to evaluate the performance of a filesystem in *bulk data transfers*. 
Specifically, we measure both *read* and *write* throughput. We define data transfers of GBs of data 
as bulk data transfers.

#### Responsiveness

The responsiveness is defined as the average time for completing an operation on a filesystem. We 
measure responsiveness to evaluate the performance of a filesystem in *small random reads/writes 
operations*, which typically consists the majority of operations on a filesystem. The operations 
include file *creation*, *read*, *write* and *deletion*. 

The responsiveness also reflects the overhead for data access in a shared file system - with a large 
number of operations, the delay incurred by each operation can accrue and become a significant 
portion of the end-to-end runtime of the application performing the operations.

#### Scalability

The scalability is reflected by 1) *the ability of growing/shrinking the storage capacity* and 2) 
*the ability of serving multiple distributed clients for concurrent reads/writes*.
 
We evaluate 1) of every filesystem qualitatively by checking whether it allows dynamic 
growing/shrinking of storage capacity and the simplicity of scaling up and down.

We evaluate 2) by measuring the throughput and responsiveness of the target filesystem as the number 
of clients increases.

#### Performance metrics

With the performance defined as above, we mainly use the following metrics to quantify the 
performance of a file system:

- Read/write throughput (MB/s)
- Operation latency (ms)
- Maximum number of concurrent clients (without crashing the filesystem or causing significant 
performance drop)
- Steps needed for growing/shrinking storage capacity

### [Benchmark Tools](tools/)

- Small-file I/O
    - [smallfile](https://github.com/distributed-system-analysis/smallfile)
- Large-file I/O
    - [fio](http://freshmeat.sourceforge.net/projects/fio)
    - [iozone](http://www.iozone.org/)

### Shared filesystem solutions

The filesystem solutions to be evaluated are listed as below:

- [x] NFSv4 (baseline)
- [x] NFS Ganesha
- [x] GlusterFS
- [x] CephFS
- [x] Ceph RBD + NFSv4
- [x] GlusterFS + NFS Ganesha

In addition, some solutions provide multiple configurations (not for performance tuning) for 
different use cases, which are likely to impact the performance, *e.g.*, the 
[GlusterFS volume type](https://docs.gluster.org/en/v3/Administrator%20Guide/Setting%20Up%20Volumes/), 
distribution of backend Ceph OSDs. 

### Frequent Asked Question

#### 1. Why do you use NFS Ganesha over GlusterFS but not Ceph?

The native GlusterFS client uses FUSE 
[[reference](https://docs.gluster.org/en/v3/Quick-Start-Guide/Architecture/#fuse)], which incurs 
overhead for context switches between user/kernel spaces and could bog down the performance. 

The alternative to access GlusterFS is using 
[libgfapi](https://staged-gluster-docs.readthedocs.io/en/release3.7.0beta1/Features/libgfapi/), 
which bypasses FUSE and thus saves the context switch overhead. NFS Ganesha is one of the projects 
that uses the library to access GlusterFS, and presumably able to bring certain performance gain. 

The [FSAL (File System Abstract Layer)](https://github.com/nfs-ganesha/nfs-ganesha/wiki/Fsalsupport) 
backend of NFS Ganesha for Ceph currently uses `libcephfs` to access CephFS, which is a layer above 
the `librados` -- the library at the heart of Ceph. Therefore, it is meaningless to run NFS Ganesha
over CephFS from the standpoint of performance, since it introduces two more layers as compared to 
mounting CephFS directly. 
[A user experience](http://lists.ceph.com/pipermail/ceph-users-ceph.com/2017-November/022474.html) 
reported in the `ceph-user` mailing list proves my intuition to some extent. 

  
