import sys,unittest,tempfile,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nao/bridge'))
from native_kicks import read_kick,JOINTS,BehaviorFuture
class NativeKickTests(unittest.TestCase):
    def file(self,value='0',extra=''):
        curves=''.join('<ActuatorCurve actuator="%s" unit="-1"><Key frame="25" value="%s"/><Key frame="50" value="%s"/></ActuatorCurve>'%(n,value,value) for n in sorted(JOINTS))
        xml='<Root><Box name="LShoot"><Timeline enable="1" fps="25"><ActuatorList model="Nao">'+curves+'</ActuatorList>'+extra+'</Timeline></Box></Root>'
        f=tempfile.NamedTemporaryFile(delete=False,suffix='.xar');f.write(xml.encode());f.close();self.addCleanup(os.unlink,f.name);return f.name
    def test_reads_complete_timeline_with_original_seconds(self):
        names,angles,times=read_kick('kick_left',self.file());self.assertEqual(set(names),JOINTS)
        self.assertTrue(all(t==[1.,2.] for t in times));self.assertTrue(all(a==[0.,0.] for a in angles))
    def test_never_executes_nested_behavior_scripts_or_curves(self):
        extra='<BehaviorLayer><Box><script>raise Exception()</script><Timeline><ActuatorList><ActuatorCurve actuator="Unknown"/></ActuatorList></Timeline></Box></BehaviorLayer>'
        self.assertEqual(len(read_kick('kick_left',self.file(extra=extra))[0]),25)
    def test_rejects_missing_side_nonfinite_and_arbitrary_name(self):
        for name in ('kick_right','arbitrary'):
            with self.assertRaises(ValueError):read_kick(name,self.file())
        for value in ('nan','inf'):
            with self.assertRaises(ValueError):read_kick('kick_left',self.file(value))

    def test_native_behavior_cancellation_stops_only_its_owned_behavior(self):
        from unittest.mock import Mock
        manager=Mock();future=BehaviorFuture(manager,'taichi-dance-free')
        future.cancel();future.cancel()
        manager.runBehavior.assert_called_once_with('taichi-dance-free',_async=True)
        manager.stopBehavior.assert_called_once_with('taichi-dance-free',_async=True)
        manager.runBehavior.return_value.cancel.assert_called_once()
