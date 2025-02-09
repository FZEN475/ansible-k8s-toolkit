# ansible-library
## Описание
Набор шаблонов для плейбуков ansible.  
_**Путь к папке шаблонов абсолютный!**_
---
## [disk_resize]()
После изменений размера диска на esxi, требуется применить изменения на NODE.  
### Example
```yaml
- hosts: servers
  gather_facts: no
  tasks:
    - name: Увеличение размера диска до максимального (include_tasks).
      ansible.builtin.include_tasks:
        file: /source/playbooks/library/disk_resize.yaml
```
---
## [apt]()
Обновление репозиториев списком.  
Добавление gpg ключей списком.  
Установка пакетов списком.  
Апгрейд по необходимости.
### Variables
* gpg_key:string[] - список ссылок на ключи.
* repository:string[] - список ссылок на репозитории.
* list:string[] - список пакетов.
* upgrade:bool - Апгрейд пакетов.

### Example
```yaml
- name: Install.
  ansible.builtin.include_tasks: /source/playbooks/library/apt.yaml
  vars:
    gpg_key:
      - "https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key"
    repository:
      - "deb https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /"
    list:
      - 'kubelet'
      - 'kubeadm'
      - 'kubectl'
    upgrade: false
```
---
## [git_pull]()
Загрузка репозитория с приватного git.
Авторизация по ключу.  
Выбор ветки и папки назначения.
Ключ авторизации должен находится в /run/secrets/  
Поиск ключа по имени.
### Variables
* key_name:string - имя ключа.
* refresh:bool - обновить ключ.
* git_url:string - ссылка (ssh).
* branch:string - ветка.
* dest:string - папка для скачивания.
### Example
```yaml
- name: Clone
  ansible.builtin.include_tasks: /source/playbooks/library/git_clone.yaml
  vars:
    key_name: "git_key"
    refresh: "false"
    git_url: "git@github.com:FZEN475/ansible-library.git"
    branch: "main"
    dest: "/tmp/"
```
## [create_CA]()
Генерация корневого CA и дочерних (серверных и клиентских) сертификатов списком.  
* Проверка существующего CA (чтобы не пересоздавать).
* Создание ключа.
* Создание запроса на подпись.
* Подписание и создание crt.
* Конвертация в pem.
* Запуск [create_chain]() Для элементов списка.
### Variables
* ca:object - { "path":"","name":"" } - путь к ca сертификатам.
  * path:string - директория.
  * name:string - название сертификата.
* list:object[] - список дочерних сертификатов.
  * path:string - директория.
  * name:string - название сертификата.
  * key_usage:string[] - назначение.
  * extended_key_usage:string[] - расширенное назначение
  * subject_alt_name:string - список DNS имён и IP
### Example
Создаёт корневой сертификат /etc/ssl/etcd/ca_etcd
```yaml
- name: ---
  ansible.builtin.include_tasks: /ansible_root/playbooks/tasks/_0_utility/cert/_0_create.yaml
  vars:
    ca: { "path":"/etc/ssl/etcd/","name":"ca_etcd" }
    list: [
      { "path":"/etc/ssl/etcd/","name":"{{loop_hostname}}",
             "key_usage":[digitalSignature],"extended_key_usage":[serverAuth,clientAuth],
             "subject_alt_name":'IP:127.0.0.1,IP:192.168.2.2,IP:192.168.2.10,{{ groups.control_all | map("regex_replace", "^(.*)$", "DNS:\1-etcd") | join(",") }},DNS:balancer'},
      { "path": "/etc/ssl/etcd/","name": "{{loop_hostname}}-peer",
        "key_usage": [ digitalSignature ],"extended_key_usage": [ serverAuth,clientAuth ],
        "subject_alt_name": 'IP:127.0.0.1,IP:192.168.2.2,IP:192.168.2.10,{{ groups.control_all | map("regex_replace", "^(.*)$", "DNS:\1-etcd") | join(",") }},DNS:balancer' },
      {"path":"/etc/ssl/etcd/","name":"client",
       "key_usage":[ keyEncipherment,dataEncipherment ],"extended_key_usage":[clientAuth],
       "subject_alt_name":''},
      { "path": "/etc/ssl/balancer/","name": "balancer",
        "key_usage": [ digitalSignature ],"extended_key_usage": [ serverAuth,clientAuth ],
        "subject_alt_name": 'IP:127.0.0.1,IP:192.168.2.2,{{ groups.control_all | map("regex_replace", "^(.*)$", "DNS:\1-etcd") | join(",") }},DNS:balancer' }]
    renew: false
  loop: "{{ groups.control_all }}"
  loop_control:
    label: "{{ loop_hostname }}"
    loop_var: loop_hostname


```












