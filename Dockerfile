FROM registry.sigma.sbrf.ru/base/redhat/rhel7:7.6

RUN localedef -c -i ru_RU -f CP1251 ru_RU.CP1251 && \
    echo "LANG=ru_RU.CP1251" > /etc/locale.conf

RUN localedef -c -i ru_RU -f UTF-8 ru_RU.UTF-8 && \
    echo "LANG=ru_RU.UTF-8" > /etc/locale.conf

ENV LANG en_US.UTF-8

# set localtimezone >> Msk
# RUN rm -f /etc/localtime
# RUN ln -s /usr/share/zoneinfo/Europe/Moscow /etc/localtime

ADD /docker/sigma/yum.repos.d/* /etc/yum.repos.d/
ADD /docker/sigma/ca-certs/* /etc/pki/ca-trust/source/anchors/
ADD /docker/sigma/pip-sigma.conf /etc/pip.conf
ADD /requirements.txt /requirements.txt
ADD /logs /logs
ADD /connectors /connectors

ENV PATH=/opt/rh/rh-python36/root/usr/bin${PATH:+:${PATH}} \
    LD_LIBRARY_PATH=/opt/rh/rh-python36/root/usr/lib64:/usr/lib/oracle/12.2/client64/lib \
    MANPATH=/opt/rh/rh-python36/root/usr/share/man:$MANPATH \
    PKG_CONFIG_PATH=/opt/rh/rh-python36/root/usr/lib64/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}} \
    XDG_DATA_DIRS="/opt/rh/rh-python36/root/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

RUN update-ca-trust force-enable & update-ca-trust extract & update-ca-trust
RUN yum install git -y
RUN git config --global user.name cab-sa-mls00001
RUN git config --global user.email swml@sberbank.ru
RUN yum install gcc gcc-c++ \
    python36 python36-devel python36-pip -y \
    postgresql-devel

RUN python3 -m pip install -r /requirements.txt -i http://mirror.sigma.sbrf.ru/pypi/simple/ --trusted-host mirror.sigma.sbrf.ru

COPY . /app
WORKDIR /app

CMD ["python", "main.py"]
