CephFS REST API
===============
The API is for Ceph volume plugin to create and manage CephFS volumes. 

The API can run as a container with the following requirements met:

- Use `host` network
- Ceph REST API must be running on the same host
- Mount the host's docker socket and specify the path as an environment variable

You can start with the command below. 

```bash 
docker run -d --name=cephfs-api --net host \
    -v /var/run/docker.sock:/var/run/docker.sock \ 
    -e DOCKER_HOST=unix://var/run/docker.sock  \
    dchampion24/cephfs-api 
```

By default, the API only listens to `localhost` since it is usually used locally by the Docker 
volume plugin. To make it listen to the public, add the following argument to the docker command 
above:

```bash
docker run -d --name=cephfs-api --net host \
    -v /var/run/docker.sock:/var/run/docker.sock \ 
    -e DOCKER_HOST=unix://var/run/docker.sock  \
    dchampion24/cephfs-api  \
    -address=0.0.0.0 
```

Other options are listed as below:

```console 
  --address                        binding address (default 127.0.0.1)
  --ceph-api-host                  The host where Ceph REST API runs on
                                   (default localhost)
  --ceph-api-port                  Port which Ceph REST API listens on (default
                                   5000)
  --ceph-config-dir                Ceph configuration directory (default
                                   /opt/ceph/etc)
  --ceph-daemon-image              Ceph daemon docker image (default
                                   ceph/daemon)
  --ceph-lib-dir                   Ceph library directory (default
                                   /opt/ceph/var/lib)
  --port                           Port to listen on (default 8080)
```