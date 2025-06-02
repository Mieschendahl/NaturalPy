# Use the official Python base image
FROM python:3.13-slim

# Install bash
RUN apt-get update && apt-get install -y bash

# Installs requirements
RUN pip install --upgrade pip && pip install openai

# Create a new user and group
RUN useradd -m user

# Switch to the new user
USER user

# Set work dir
WORKDIR /home/user/naturalpy

# Copy files
COPY --chown=user:user . .

# Install package
RUN pip install .

# Set work dir
WORKDIR /home/user/naturalpy/examples

# Start an interactive bash shell by default
CMD ["bash"]