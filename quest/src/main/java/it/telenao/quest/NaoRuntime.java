package it.telenao.quest;

/** Find a working native qi/Pillow runtime without changing robot software. */
final class NaoRuntime {
    private static final String ENV="env PYTHONPATH=\"/opt/aldebaran/lib/python2.7/site-packages:$PYTHONPATH\" LD_LIBRARY_PATH=\"/opt/aldebaran/lib:$LD_LIBRARY_PATH\" ";
    static boolean supports(String version){
        try{String[] parts=version.split("\\.");return parts.length>=2&&parts[0].equals("2")&&parts[1].matches("[0-9]+")&&Integer.parseInt(parts[1])>=1&&Integer.parseInt(parts[1])<=8;}
        catch(Exception invalid){return false;}
    }
    static String run(String runtime,String arguments){
        if(!runtime.matches("python(?:2(?:\\.7)?|3)?"))throw new IllegalArgumentException("Invalid Python runtime");
        return ENV+runtime+" "+arguments;
    }
    static String probe(){
        String code="import sys,json; import qi; from PIL import Image; s=qi.Session(); s.connect(\"tcp://127.0.0.1:9559\"); print(json.dumps({\"python\":sys.argv[1],\"version\":s.service(\"ALSystem\").systemVersion(_async=True).value(3000)}))";
        return "for runtime in python2.7 python2 python python3; do if command -v \"$runtime\" >/dev/null 2>&1; then "+ENV+"\"$runtime\" -c '"+code+"' \"$runtime\" 2>/dev/null && exit 0; fi; done; exit 1";
    }
}
