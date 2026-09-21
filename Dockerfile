# =====================================================================
# EE Calculator — single self-contained HTML page (build_page.py already
# inlines the theme CSS + fonts), so serving it is just static nginx. No
# app process, no state, no volume: the image is the whole deploy.
# =====================================================================
FROM nginx:1.27-alpine

COPY EE_Calculator.html /usr/share/nginx/html/index.html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:80/ || exit 1
