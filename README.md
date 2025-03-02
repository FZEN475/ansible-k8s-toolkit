# ansible-library
## Description
Набор шаблонов для плейбуков ansible.  
_**Путь к папке шаблонов `/source/playbooks/library/` **_
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
* `gpg_key:string[]` - список ссылок на ключи.
* `repository:string[]` - список ссылок на репозитории.
* `list:string[]` - список пакетов.
* `upgrade:bool` - Апгрейд пакетов.

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
* `key_name:string` - имя ключа.
* `refresh:bool` - обновить ключ.
* `git_url:string` - ссылка (ssh).
* `branch:string` - ветка.
* `dest:string` - папка для скачивания.
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
* `ca:object` - путь к ca сертификатам.
  * `path:string` - директория.
  * `name:string` - название сертификата.
* `list:object[]` - список дочерних сертификатов.
  * `path:string` - директория.
  * `name:string` - название сертификата.
  * `key_usage:string[]` - назначение.
  * `extended_key_usage:string[]` - расширенное назначение
  * `subject_alt_name:string` - список DNS имён и IP
* `renew:bool` - пересоздание НЕ CA сертификатов.
### Example
На примере сертификатов для etcd
```yaml
- name: dns_names
  set_fact:
    dns_names: "{{ groups.control_all | map('regex_replace', '^(.*)$', 'DNS:\\1-etcd') | join(',') }}"

- name: Cert config for etcd and peers
  set_fact:
    cert_servers_conf_list: |
      {{ cert_servers_conf_list|default([]) + [
        { "path":"/etc/ssl/etcd/","name":loop_hostname,
          "key_usage":["digitalSignature"],"extended_key_usage":["serverAuth","clientAuth"],
          "subject_alt_name":"IP:127.0.0.1,IP:192.168.2.2," + dns_names + ",DNS:balancer"
        },
        { "path": "/etc/ssl/etcd/","name": (loop_hostname+"-peer"),
          "key_usage": [ "digitalSignature" ],"extended_key_usage": [ "serverAuth","clientAuth" ],
          "subject_alt_name": "IP:127.0.0.1,IP:192.168.2.2," + dns_names + ",DNS:balancer" 
        }]
      }}
  loop: "{{ groups.control_all }}"
  loop_control:
    label: "{{ loop_hostname }}"
    loop_var: loop_hostname

- name: Add client and balancer certs configs
  set_fact:
    cert_all_conf_list: |
      {{ cert_servers_conf_list|default([]) + [      
        { "path":"/etc/ssl/etcd/","name":"client",
          "key_usage":[ "keyEncipherment","dataEncipherment" ],"extended_key_usage":["clientAuth"],
          "subject_alt_name":""
        },
        { "path": "/etc/ssl/balancer/","name": "balancer",
          "key_usage": [ "digitalSignature" ],"extended_key_usage": [ "serverAuth","clientAuth" ],
          "subject_alt_name": "IP:127.0.0.1,IP:192.168.2.2," + dns_names + ",DNS:balancer" 
        }]
      }}

- name: ---
  ansible.builtin.include_tasks: /source/playbooks/library/create_CA.yaml
  vars:
    ca: { "path":"/etc/ssl/etcd/","name":"ca_etcd" }
    list: "{{ cert_all_conf_list }}"
    renew: false
```
## [create_chain]()
Создаются сертификаты для каждого элемента списка и подписываются CA.
* Проверка существующего сертификата.
* Создание ключа.
* Создание запроса на подпись.
* Подписание СФ и создание crt.
* Конвертация в pem.
* Если renew = true то создание принудительно.
### Variables
* `ca:object` - путь к ca сертификатам.
  * `path:string` - директория.
  * `name:string` - название сертификата.
* `list:object[]` - список дочерних сертификатов.
  * `path:string` - директория.
  * `name:string` - название сертификата.
  * `key_usage:string[]` - назначение.
  * `extended_key_usage:string[]` - расширенное назначение
  * `subject_alt_name:string` - список DNS имён и IP
* `renew:bool` - пересоздание НЕ CA сертификатов.
### Example
```yaml
- name: ---
  ansible.builtin.include_tasks: /source/playbooks/library/create_chain.yaml
  vars:
    item_renew: "true"
    path_ca: "{ 'path':'/etc/ssl/etcd/','name':'ca_etcd' }"
  with_items: |
      [{ "path": "/etc/ssl/server/","name": "server",
        "key_usage": [ "digitalSignature" ],"extended_key_usage": [ "serverAuth","clientAuth" ],
        "subject_alt_name": "IP:127.0.0.1,DNS:server" 
      }]
```
## [add_vault_secret]()
Создание секретов (списком) в [Vault]() и Store, для дальнейшего использования.
* Создание ConfigMap с curl скриптами для Vault.
* Создание Job выполняющего скрипты.
* Создание SecretStore\ClusterSecretStore.
* Создание ExternalSecrets.
### Variables
`Переменные ":*" - обязательные`
* `ns:string:*` - пространство имён.
* `resource:string:*` - название проекта.
* `secret_name:string [default: {{ resource }}-secrets]`- название секрета в kubernetes.
* `cluster_access:bool` - SecretStore\ClusterSecretStore
* `sa:string [default: {{ resource }}-sa]` - ServiceAccount, которому разрешен доступ к секретам.
* `store_name:string [default: {{ resource }}-ss/{{ resource }}-css]` - Имя SecretStore, если требуется получить доступ к существующему секрету.
* `list:object[]:*` - Список секретов.
  * `key:string:*` - Ключ секрета в Vault.
  * `vault:bool` - Создать или обновить секрет в Vault.
  * `value:string` - Значение секрета.
  * `secretKey:string [default: key]` - Имя секрета в kubernetes
  * `path:string [default: {{ ns }}/{{ resource }}/{{ s_name }}]` - путь к секрету в Vault.
  * `decodingStrategy:string [default: None]` - Метод расшифровки секрета при получении из Vault.
* `data:object{}` - Шаблон секрета при получении из Vault.
* `es_type:string [default: Opaque]` - Тип секрета kubernetes.
### Dependency
* [cert-manager]()
* [trust-manager]()
* [Vault]()
### Example 1
Создать секрет в пространстве test1 с шаблоном. 
```yaml
- name: secret facts
  ansible.builtin.set_fact:
    secret_template1:
      postgres: !unsafe |
        postgresql-primary.storage.svc:5432:*:postgres:{{ .postgres }}
- name: secret facts
  ansible.builtin.set_fact:
    secrets1:
      - { ns: "test1", resource: "test", secret_name: "test-renamed", data: "{{ secret_template1 }}",
          cluster_access: true, sa: "test-sa", store_name: "test-css", es_type: "Opaque",
          list: [
            { "vault": true, "key": "postgres-password", "secretKey": "postgres", 
              "value": "{{ lookup('ansible.builtin.file', '/run/secrets/pgsql_password') }}",
              "path": "test/test/test-renamed", "decodingStrategy": "None"
            },
            { "vault": true, "key": "replication-password", "secretKey": "replication_postgres",
              "value": "{{ lookup('ansible.builtin.password', '/dev/null', chars=['ascii_lowercase', 'digits'], length=8) | b64encode }}",
              "path": "test/test/test-renamed", "decodingStrategy": "Base64"
            }
          ]}
```
### Example 2
Получить существующий секрет в пространстве test2 из Vault. У ServiceAccount есть дополнительный доступ к секретам базы данных.
```yaml
- name: secret facts
  ansible.builtin.set_fact:
    secret_template2:
      postgres: !unsafe |
        {{ .postgres }}
      database-static: !unsafe |
        {{ .database_static }}
- name: secret facts
  ansible.builtin.set_fact:
    secrets1:
      - { ns: "test2", resource: "test", secret_name: "test-renamed", data: "{{ secret_template2 }}",
          sa: "test-sa", store_name: "test-css", es_type: "kubernetes.io/dockerconfigjson",
          list: [
            { "vault": true, "key": "postgres-password", "secretKey": "postgres", 
              "path": "test/test/test-renamed", "decodingStrategy": "None"
            },
            { "vault": true, "key": "database-static", "secretKey": "database_static",
              "path": "database/static-creds/test"
            }
          ]}
```