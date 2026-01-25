---
trigger: always_on
---

1. Los tests se deben hacer con pytest.
2. Todos los tests se debem incluir en la carpeta tests.
3. En los tests mete loggers.
4. Sigue una arquitectura limpia en la carpeta tests, separalo por responsabilidades, por ejemplo:
/llm
    test_agent.py
    ...
/scanner
    test_database.py
    ...
y asi con todos.