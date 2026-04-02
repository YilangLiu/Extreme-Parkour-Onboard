# For deployment (ARM64) - build separately
FROM dustynv/ros:humble-pytorch-l4t-r35.3.1
# FROM ros:humble-ros-base

# Use standard Ubuntu + ROS Humble base image for x86_64 (local development)
# FROM osrf/ros:humble-desktop-full
# To make sure installing tzdata will not prompt questions
ARG DEBIAN_FRONTEND=noninteractive

# ROS GPG KEY FIX
RUN sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

RUN apt-get update && apt-get install -y --no-install-recommends \
    zsh neovim tmux git htop curl wget \
    net-tools iputils-ping\
    python3-pip \
    python3-tk \
    # init certificate for curl
    ca-certificates \
    # For x11 forwarding tests (xeyes, xclock etc.)
    x11-apps \
    # For pytorch
    libopenblas-dev \
    cmake sudo \
    software-properties-common

ARG USERNAME=real
# Defaults make plain `docker build` work too; devcontainer overrides these.
ARG USER_UID=1000
ARG USER_GID=1000


# Add the new user (userid should be consistent to the one in the host machine)
# Change the password to "real". You can use other password by changing the following line
RUN groupadd -g ${USER_GID} ${USERNAME} && \
    useradd ${USERNAME}  -u ${USER_UID} -g ${USER_GID} -m -p "$(openssl passwd -1 real)"
# Add sudo access (not recommended, but is hulepful for development)
RUN getent group video || groupadd video && \
    getent group render || groupadd render && \
    usermod -aG sudo,video,render ${USERNAME}
# Give ownership of the user's home directory to the new user
RUN chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}
USER ${USERNAME}
# Set the user's home directory as the working directory
WORKDIR /home/${USERNAME}


############### Development Tools ###############

# install and setup zsh (with oh-my-zsh and plugins)
# Make oh-my-zsh install non-interactive for Docker builds
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" 
ARG PLUGIN_DIR=/home/${USERNAME}/.oh-my-zsh/custom/plugins/
RUN git clone https://github.com/marlonrichert/zsh-autocomplete.git $PLUGIN_DIR/zsh-autocomplete && \
    git clone https://github.com/zsh-users/zsh-autosuggestions $PLUGIN_DIR/zsh-autosuggestions  && \
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git $PLUGIN_DIR/zsh-syntax-highlighting

# Set up zsh plugins and theme
# And some key bindings: ctrl-R to search in the history, ctlr-backspace to delete a word, etc.
RUN mv /home/${USERNAME}/.zshrc /home/${USERNAME}/.zshrc.bak && \
    echo 'export ZSH="$HOME/.oh-my-zsh"\nplugins=(\n  git\n  zsh-autosuggestions\n  zsh-autocomplete\n  zsh-syntax-highlighting\n  themes\n)\n' >> /home/${USERNAME}/.zshrc && \
    echo 'ZSH_THEME="eastwood"\nsource $ZSH/oh-my-zsh.sh' >> /home/${USERNAME}/.zshrc && \
    echo 'bindkey -M menuselect "\\r" .accept-line' >> /home/${USERNAME}/.zshrc && \
    echo 'bindkey -M menuselect -s "^R" "^_^_^R" "^S" "^_^_^S"' >> /home/${USERNAME}/.zshrc && \
    echo 'bindkey -M menuselect "\\e[D" .backward-char "\\eOD" .backward-char "\\e[C" .forward-char "\\eOC" .forward-char' >> /home/${USERNAME}/.zshrc && \
    echo "bindkey '^H' backward-kill-word" >> /home/${USERNAME}/.zshrc

USER ${USERNAME}
# Install unitree ros
RUN git clone https://github.com/unitreerobotics/unitree_ros2.git && \
    cd unitree_ros2/cyclonedds_ws/src && \
    git clone https://github.com/ros2/rmw_cyclonedds -b humble && \
    git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x && \
    git clone https://github.com/ros2/rosidl_dds -b humble && \
    cd .. && \
    colcon build --packages-select cyclonedds

RUN cd unitree_ros2/cyclonedds_ws && \
    pip install empy==3.3.2 catkin_pkg pyparsing lark && \
    /bin/zsh -c "source /opt/ros/humble/install/setup.zsh && \
        colcon build --packages-select rosidl_generator_dds_idl && \
        source install/setup.zsh && \
        colcon build"



RUN sed -i "s/\\\\\\\\/\\\\/g" /home/${USERNAME}/.zshrc && \
    sed -i "s/\\\\n/\\n/g" /home/${USERNAME}/.zshrc


# Install the customized unitree sdk for 
# 1) a python module to calculate CRC code for ros2 packages
# 2) a script to disable sports mode of Go2
USER ${USERNAME}
RUN git clone https://github.com/yihuai-gao/unitree_sdk2.git && \
    git clone https://github.com/unitreerobotics/unitree_sdk2_python.git && \
    cd unitree_sdk2 && \
    git checkout 92506a409843c78be358d761d19aa254053a045f && \
    mkdir build && cd build && \
    cmake .. && make -j$(($(nproc)-1)) && \
    pip install pybind11 && \
    cd ../python && mkdir build && cd build &&  \
    cmake .. -DPYBIND_PATH=$(pip show pybind11 | grep Location | cut -d' ' -f2) && \
    make -j$(($(nproc)-1)) && \
    echo "export PYTHONPATH=\$PYTHONPATH:/home/${USERNAME}/unitree_sdk2/python" >> /home/${USERNAME}/.zshrc

USER root
RUN cd /home/${USERNAME}/unitree_sdk2 && \
    ./install.sh

# Manually build and install CycloneDDS C library
WORKDIR /opt
RUN git clone --branch 0.10.2 https://github.com/eclipse-cyclonedds/cyclonedds.git \
	&& cd cyclonedds \
	&& mkdir build && cd build \
	&& cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local \
	&& make -j$(nproc) \
	&& make install

ARG CMAKE_PREFIX_PATH=""
ENV CMAKE_PREFIX_PATH=/usr/local:$CMAKE_PREFIX_PATH
# Set environment variable so CMake can locate the installed CycloneDDS
RUN echo "export CMAKE_PREFIX_PATH=/usr/local:$CMAKE_PREFIX_PATH" >> /home/${USERNAME}/.zshrc && \
    cd /home/${USERNAME}/unitree_sdk2_python && \
    pip install -e .

USER root

RUN echo "source /opt/ros/humble/install/setup.zsh" >> /home/${USERNAME}/.zshrc && \
    echo "source /home/\${USERNAME}/unitree_ros2/cyclonedds_ws/install/setup.zsh" >> /home/${USERNAME}/.zshrc && \
    echo "export CYCLONEDDS_URI=/home/\${USERNAME}/unitree_ros2/cyclonedds_ws/src/cyclonedds.xml" >> /home/${USERNAME}/.zshrc && \
    sed -i "s/enp2s0/eth1/g; s/eth0/eth1/g" /home/${USERNAME}/unitree_ros2/cyclonedds_ws/src/cyclonedds.xml

# ros2_numpy (Humble) — build from source so `import ros2_numpy` works
# Focal has no ros-humble-* debs. transforms3d from PyPI; tf_transformations from DLu (not on PyPI as tf-transformations).
USER ${USERNAME}
RUN pip install --no-cache-dir transforms3d "git+https://github.com/DLu/tf_transformations.git" && \
    mkdir -p /home/${USERNAME}/ros2_numpy_ws/src && \
    cd /home/${USERNAME}/ros2_numpy_ws/src && \
    git clone -b humble --depth 1 https://github.com/Box-Robotics/ros2_numpy.git && \
    cd /home/${USERNAME}/ros2_numpy_ws && \
    /bin/zsh -c "source /opt/ros/humble/install/setup.zsh && \
        colcon build --packages-select ros2_numpy --cmake-args -DBUILD_TESTING=OFF"

USER root
RUN echo "source /home/\${USERNAME}/ros2_numpy_ws/install/setup.zsh" >> /home/${USERNAME}/.zshrc

RUN echo 'if [ -e /dev/nvmap ] && [ ! -r /dev/nvmap ]; then echo "[WARN] /dev/nvmap is not readable for $(whoami). CUDA may fail. Try --user root or adjust device permissions/groups."; fi' >> /home/${USERNAME}/.zshrc
# Install ApproximateFoRL dependencies
RUN pip install \
    hydra-core \
    hydra-colorlog \
    pyglet \
    # gymnasium \
    wandb \
    # transforms3d \
    filterpy \
    numba \
    omegaconf \
    gitpython \
    zarr \
    rich \
    python-socketio \
    eventlet \
    pynput \
    matplotlib \ 
    seaborn

USER root

RUN apt-get update && \
    apt-get install -y git zsh curl git vim net-tools wget htop \
    x11-apps neofetch build-essential libboost-all-dev libeigen3-dev && \
    apt-get install libtinyxml2-dev libcppunit-dev liborocos-kdl-dev liburdfdom-dev iproute2 -y
RUN ln -s /usr/include/eigen3/Eigen /usr/local/include/Eigen

RUN git clone https://github.com/ros/kdl_parser.git && \
    cd kdl_parser && \
    git checkout 74d4ee3bc6938de8ae40a700997baef06114ea1b && \
    cd kdl_parser && \
    sed -i 's/kdl_parser\/visibility_control.hpp/visibility_control.hpp/g' include/kdl_parser/kdl_parser.hpp && \
    mkdir build && cd build && \
    cmake .. && make -j$(($(nproc)-1)) && make install

USER root

# Setup spacenav and rosbag2 storage
RUN apt-get update && \
    # apt-get install -y ros-humble-rosbag2-storage-mcap && \
    apt-get install -y libspnav-dev spacenavd

USER ${USERNAME}

# Copy project packages and deploy models into the image.
# At runtime, bind-mounting the repo at the same path lets you override with live code.
COPY --chown=${USERNAME}:${USERNAME} rsl_rl /home/${USERNAME}/Extreme-Parkour-Onboard/rsl_rl
COPY --chown=${USERNAME}:${USERNAME} traced /home/${USERNAME}/Extreme-Parkour-Onboard/traced
COPY --chown=${USERNAME}:${USERNAME} run_extreme_parkour.py /home/${USERNAME}/Extreme-Parkour-Onboard/
COPY --chown=${USERNAME}:${USERNAME} sport_api_constants.py /home/${USERNAME}/Extreme-Parkour-Onboard/
COPY --chown=${USERNAME}:${USERNAME} unitree_ros2_real.py /home/${USERNAME}/Extreme-Parkour-Onboard/
COPY --chown=${USERNAME}:${USERNAME} visual_extreme_parkour.py /home/${USERNAME}/Extreme-Parkour-Onboard/
RUN cd /home/${USERNAME}/Extreme-Parkour-Onboard/rsl_rl && pip install -e .

RUN pip install pyrealsense2 
RUN pip install opencv-python opencv-contrib-python
WORKDIR /home/${USERNAME}
