FROM ghcr.io/open-webui/open-webui:latest
EXPOSE 8080
ENV HOST=0.0.0.0
CMD ["./start.sh"]
