import UnityPy, os
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
AA='romfs/Data/StreamingAssets/aa/Switch'
def load(*names):
    g=TypeTreeGenerator('6000.0.76f1'); g.load_local_dll_folder('dump/DummyDll')
    paths=[os.path.join(AA,f) for f in os.listdir(AA)]
    env=UnityPy.load(*paths); env.typetree_generator=g
    return env
