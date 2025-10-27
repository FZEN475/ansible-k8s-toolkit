

Шаблон для gpt
```yaml
- name: Validate input parameters
  block:
    < для параметров или логических групп параметров >
    - name: Validate <описание>

      assert:
        that:
          [ <Список правил> ] 
        fail_msg: "Ошибка: <Описание ошибки>" 
        success_msg: "<Параметры> проверены успешно."
```

Заполни условия валидации по шаблону 
Группируй по смыслу






```shell
curl \
  --header "X-Vault-Token: $VAULT_TOKEN" \
  --request GET \
  "$VAULT_ADDR/v1/auth/kubernetes/role/test"
```