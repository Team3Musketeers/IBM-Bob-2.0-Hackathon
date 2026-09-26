FROM nginx:alpine

# Build context is this directory (see docker-compose.yml).
COPY static/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
