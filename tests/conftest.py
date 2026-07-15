"""
Pré-importe les modules memory/* qui exposent des classes testées directement
(tests/memory/*), pour que les guards `if mod_path not in sys.modules` des
_stub_memory() de tests/api/test_streaming.py et test_upload.py les trouvent
déjà réels et ne les remplacent pas par un module factice vide — ce qui ferait
échouer l'import de CodebaseRepository/BizContextRepository/SharedMemoryRepository
selon l'ordre de collecte des tests.

Import sans effet de bord réseau : la construction de QdrantVectorStore()
(memory.store.get_client() -> QdrantClient(...)) ne se connecte pas
tant qu'aucune méthode n'est appelée.
"""

import memory.biz_manager.context  # noqa: F401
import memory.dev_senior.retriever  # noqa: F401
import memory.shared.memory  # noqa: F401
