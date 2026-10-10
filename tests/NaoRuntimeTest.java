package it.telenao.quest;
public class NaoRuntimeTest {
    public static void main(String[] args){
        for(String version:new String[]{"2.1.4.13","2.5.5.5","2.8.7.4"})if(!NaoRuntime.supports(version))throw new AssertionError(version);
        for(String version:new String[]{"1.14.0","2.9.0","3.0.0","2.x","2.0",""})if(NaoRuntime.supports(version))throw new AssertionError(version);
        for(String runtime:new String[]{"python2.7","python2","python","python3"})NaoRuntime.run(runtime,"/home/nao/telenao/manage.py check");
        try{NaoRuntime.run("python; unexpected","check");throw new AssertionError("Unsafe interpreter accepted");}catch(IllegalArgumentException expected){}
        System.out.println("PASS NAOqi 2.1-2.8 runtime selection and bounded interpreter names");
        if(args.length>0&&args[0].equals("probe"))System.out.print(NaoRuntime.probe());
    }
}
