#! /usr/bin/env bash
sudo apt-get install qemu binfmt-support qemu-user-static # Install the qemu packages
sudo apt install qemu-user qemu-user-static gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu binutils-aarch64-linux-gnu-dbg build-essential
sudo docker run --rm --privileged multiarch/qemu-user-static --reset -p yes # This step will execute the registering scripts
docker run --rm -t arm64v8/ubuntu uname -m
# add docker-container driver to buildx
docker buildx ls
docker buildx create --name my-multiarch-builder
docker buildx use my-multiarch-builder
docker buildx inspect --bootstrap
docker buildx ls
docker buildx inspect --bootstrap