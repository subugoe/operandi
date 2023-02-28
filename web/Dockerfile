FROM golang:1.20-alpine3.17 AS builder

LABEL maintainer="panzer@sub.uni-goettingen.de"

ARG DEBUG=false
ARG GC_FLAGS="all=-N -l"

# install build essentials
RUN apk --update upgrade && \
    apk add --no-cache busybox gcc libc-dev

RUN mkdir -p /go/src/web

WORKDIR /go/src/web

RUN echo $PWD

COPY . .

# Copy and download go dependencies
RUN go get -u . 
RUN go mod download

RUN go build -o goapp

WORKDIR /usr/local/bin/

# Copy binary from build to main folder
RUN cp /go/src/web/goapp ./web

# Build a optimized image
FROM alpine:3.17

COPY --from=builder /usr/local/bin/web /usr/local/bin/web
