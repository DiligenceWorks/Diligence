FROM postgres:16-alpine

# Force trust authentication regardless of environment variables
RUN echo "#!/bin/bash" > /docker-entrypoint-initdb.d/00-trust-auth.sh && \
    echo 'echo "host all all 0.0.0.0/0 trust" > "$PGDATA/pg_hba.conf"' >> /docker-entrypoint-initdb.d/00-trust-auth.sh && \
    echo 'echo "local all all trust" >> "$PGDATA/pg_hba.conf"' >> /docker-entrypoint-initdb.d/00-trust-auth.sh && \
    chmod +x /docker-entrypoint-initdb.d/00-trust-auth.sh

ENV POSTGRES_USER=fitness
ENV POSTGRES_DB=fitness_rewards
ENV POSTGRES_HOST_AUTH_METHOD=trust
