FROM ipfs/go-ipfs:latest
COPY .ipfs/swarm.key /data/ipfs/swarm.key
COPY init.sh /usr/local/bin/start_ipfs
RUN chmod 777 /usr/local/bin/start_ipfs
RUN chown ipfs:users /usr/local/bin/start_ipfs && chmod +x /usr/local/bin/start_ipfs
