FROM apache/kafka:3.7.2
USER root
COPY topics-init.sh /usr/local/bin/topics-init.sh
RUN chmod +x /usr/local/bin/topics-init.sh

# Wrap upstream start: background broker, wait healthy, run init, then foreground wait
COPY docker-entrypoint-init.sh /usr/local/bin/docker-entrypoint-init.sh
RUN chmod +x /usr/local/bin/docker-entrypoint-init.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint-init.sh"]