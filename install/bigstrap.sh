#!/bin/bash

SIRIUS_BRANCH=master

for i in "$@"
do
    case $i in
        -sb=* | --sirius-branch=*)    SIRIUS_BRANCH="${i#*=}"
                                     shift
                                     ;;
        -h | --help )                echo "Установка виртуального окружения и клонирование проектов.
Ветки приложений по умолчанию
 * sirius - master
Можно переопределить через передаваемые аргументы
 -sb=    --sirius-branch="
                                     exit
                                     ;;
    esac
done


# 0. Создать корневую директорию инсталляции (допустим, /srv/infrastructure). Дальше все пути будут относительно корневой директории

# 0. Скопировать конфигурационный файл
cp install/usagi.yaml usagi.local.yaml

# 1. Создать базовые поддиректории, в которые всё будет соваться
mkdir code
mkdir configs
mkdir logs

# 2. Создать Virtualenv и активировать его
virtualenv venv
. venv/bin/activate
pip install pip setuptools --upgrade

pip install pyyaml jinja2

# 3. Склонировать сервисы
echo " -> sirius branch: ${SIRIUS_BRANCH}"
git clone https://stash.bars-open.ru/scm/medvtr/sirius.git -b ${SIRIUS_BRANCH} code/sirius

# 4. Установить зависимости (prod или test, или dev)
pip install -r code/sirius/requirements/prod.txt
pip install -r code/sirius/requirements/usagi.txt

pip install git+https://stash.bars-open.ru/scm/medvtr/hitsl.utils.git@develop#egg=hitsl_utils
pip install git+https://stash.bars-open.ru/scm/medvtr/tsukino_usagi.git@master#egg=tsukino_usagi
pip install git+https://stash.bars-open.ru/scm/medvtr/pysimplelogs2.git@master#egg=pysimplelogs2
