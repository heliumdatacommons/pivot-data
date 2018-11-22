Relevant docs
=============

### 0. Docker
- [Docker SDK](https://docker-py.readthedocs.io/en/stable/)

### 1. Ceph data locality 

#### 1.1 Find an OSD 
```console
$ ceph osd find osd.0
{
    "osd": 0,
    "ip": "10.52.100.3:6801/17116",
    "crush_location": {
        "datacenter": "gcp-us-east1-b",
        "host": "benchmark-us-east1-b-cephfs-1",
        "region": "gcp-us-east1",
        "root": "default"
    }
}

$ curl -X GET http://localhost:5000/api/v0.1/osd/find?id=osd.0
{
    "osd": 0,
    "ip": "10.52.100.3:6801/17116",
    "crush_location": {
        "datacenter": "gcp-us-east1-b",
        "host": "benchmark-us-east1-b-cephfs-1",
        "region": "gcp-us-east1",
        "root": "default"
    }
}
```

#### 1.2 Find location of a file
```console
$ ceph osd map alpha_data crushmap
osdmap e326 pool 'alpha_data' (61) object 'crushmap' -> pg 61.6e86c5f (61.7) -> up ([1,0], p1) acting ([1,0], p1)

$ curl -X GET -H "Accept: application/json" "http://localhost:5000/api/v0.1/osd/map?pool=alpha_data&object=crushmap"
{"status": "OK", "output": {"acting_primary": 1, "up_primary": 1, "pgid": "61.7", "pool_id": 61, "up": [1, 0], "epoch": 326, "objname": "crushmap", "acting": [1, 0], "raw_pgid": "61.6e86c5f", "pool": "alpha_data"}}
```

#### 1.3 Get and decompile the CRUSH map
```console
$ ceph osd getcrushmap | crushtool -d - -o crushmap
41
```

#### 1.4 Compile and update the CRUSH map
```console
$ crushtool -c crushmap -o crushmap.bin                                                                                                                                                               
$ ceph osd setcrushmap -i crushmap.bin
42
```

#### 1.5 Get CRUSH rules
```console
$ ceph osd crush rule ls
replicated_rule
region_us_east1_rule

$ curl -X GET -H "Accept: application/json" "http://localhost:5000/api/v0.1/osd/crush/rule/ls"
{"status": "OK", "output": ["replicated_rule", "region_us_east1_rule"]}centos@benchmark-us-east1-b-cephfs-1:~$ 
```

### 2. Ceph data pool

#### 2.1 Create a data pool
```console
$ ceph osd pool create alpha_data 8 8 replicated region_us_east1_rule 0
pool 'alpha_data' created'

$ 
```

#### 2.2 Set replication factor
```console
$ ceph osd pool set alpha_data size 1
set pool 61 size to 1
$ rados -p alpha_data put a.file a.file
$ ceph osd map alpha_data a.file
osdmap e331 pool 'alpha_data' (61) object 'a.file' -> pg 61.4b7d01bc (61.4) -> up ([1], p1) acting ([1], p1)

$ curl -X PUT -H "Accept:application/json" "http://localhost:5000/api/v0.1/osd/pool/set?pool=alpha_data&var=size&val=1"
{"status": "set pool 61 size to 1", "output": []}
```

### References
1. [A crash course in CRUSH by Sage Weil](https://www.slideshare.net/sageweil1/a-crash-course-in-crush)
2. [Scalable placement of replicated data in Ceph](https://javiermunhoz.com/blog/2016/04/30/scalable-placement-of-replicated-data-in-ceph.html)