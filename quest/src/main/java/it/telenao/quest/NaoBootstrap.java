package it.telenao.quest;

import android.app.Activity;
import android.app.AlertDialog;
import com.jcraft.jsch.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Properties;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import org.json.JSONObject;

/** Owner-authorized setup and manual start, directly from Quest to the robot. */
final class NaoBootstrap {
    private static final String ROOT="/home/nao/telenao";
    interface Listener {void progress(String message);void ready(String pairing);void failed(String message);}
    private static String read(InputStream in)throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] bytes=new byte[4096];int n;
        while((n=in.read(bytes))!=-1){if(out.size()+n>1048576)throw new IOException("Robot reply too large");out.write(bytes,0,n);}
        return new String(out.toByteArray(),StandardCharsets.UTF_8);
    }
    private static String exec(Session session,String command)throws Exception {
        ChannelExec channel=(ChannelExec)session.openChannel("exec");channel.setCommand(command);channel.setInputStream(null);
        ByteArrayOutputStream errors=new ByteArrayOutputStream();channel.setErrStream(errors);InputStream in=channel.getInputStream();
        channel.connect(5000);
        try{
            String text=read(in);long deadline=System.currentTimeMillis()+2000;
            while(!channel.isClosed()&&System.currentTimeMillis()<deadline)Thread.sleep(20);
            if(channel.getExitStatus()!=0){String error=errors.toString("UTF-8");if(error.contains("No module named"))throw new IOException("NAO is missing Python qi or Pillow. Check its runtime before this trial.");throw new IOException(text.trim().isEmpty()?"Robot command failed":text.trim());}
            return text;
        }finally{channel.disconnect();}
    }
    private abstract static class Auth implements UserInfo,UIKeyboardInteractive {
        private final String secret;Auth(String value){secret=value;}
        public String getPassphrase(){return null;}public String getPassword(){return secret;}
        public boolean promptPassword(String message){return true;}public boolean promptPassphrase(String message){return false;}
        public String[] promptKeyboardInteractive(String destination,String name,String instruction,String[] prompt,boolean[] echo){return prompt.length==1&&echo.length==1&&!echo[0]?new String[]{secret}:null;}
    }
    static void connect(Activity activity,String head,String user,String password,Listener listener){
        new Thread(()->{
            Session session=null;ChannelSftp sftp=null;
            try{
                listener.progress("Connecting to NAO...");
                JSch jsch=new JSch();File known=new File(activity.getFilesDir(),"telenao_known_hosts");if(!known.exists())known.createNewFile();jsch.setKnownHosts(known.getAbsolutePath());
                session=jsch.getSession(user,head,22);session.setPassword(password);
                Properties options=new Properties();options.put("StrictHostKeyChecking","ask");options.put("PreferredAuthentications","keyboard-interactive,password");session.setConfig(options);
                session.setUserInfo(new Auth(password){
                    public void showMessage(String message){listener.progress("Checking robot identity...");}
                    public boolean promptYesNo(String message){
                        CountDownLatch done=new CountDownLatch(1);boolean[] yes={false};
                        activity.runOnUiThread(()->{if(activity.isFinishing()){done.countDown();return;}new AlertDialog.Builder(activity).setTitle("Pair with your NAO")
                            .setMessage(message).setPositiveButton("Pair",(dialog,which)->{yes[0]=true;done.countDown();})
                            .setNegativeButton("Cancel",(dialog,which)->done.countDown()).setOnCancelListener(dialog->done.countDown()).show();});
                        try{done.await(60,TimeUnit.SECONDS);}catch(InterruptedException interrupted){Thread.currentThread().interrupt();}
                        return yes[0];
                    }
                });
                session.connect(10000);session.setTimeout(45000);
                listener.progress("Checking NAOqi version and camera runtime...");
                JSONObject environment;
                try{environment=new JSONObject(exec(session,NaoRuntime.probe()).trim());}
                catch(Exception unavailable){throw new IOException("No usable robot Python runtime with qi and Pillow. Check the robot SDK environment.");}
                String version=environment.getString("version"),runtime=environment.getString("python");
                if(!NaoRuntime.supports(version))throw new IOException("Requires NAOqi 2.1-2.8 with Python qi/Pillow; found "+version);
                NaoRuntime.run(runtime,"");
                sftp=(ChannelSftp)session.openChannel("sftp");sftp.connect(5000);
                String pairing="";boolean installed=false;
                try{try(InputStream in=sftp.get(ROOT+"/.telenao-token")){pairing=read(in).trim();}installed=pairing.matches("[0-9a-f]{32,80}");}catch(SftpException missing){}
                // Preserve the pairing from earlier app releases while migrating
                // the private token filename. Search only our own service folder.
                if(!installed)try{
                    for(Object entry:sftp.ls(ROOT)){
                        String name=((ChannelSftp.LsEntry)entry).getFilename();
                        if(!name.startsWith(".tele")||!name.endsWith("-token"))continue;
                        try(InputStream in=sftp.get(ROOT+"/"+name)){String candidate=read(in).trim();if(candidate.matches("[0-9a-f]{32,80}")){pairing=candidate;installed=true;break;}}
                    }
                }catch(SftpException missingFolder){}
                if(installed){
                    String manager=ROOT+"/manage.py";
                    try{sftp.stat(manager);}catch(SftpException legacy){manager=ROOT+"/manage25.py";}
                    // The manager refuses to stop an armed or preparing robot.
                    // Every CONNECT installs this APK's bridge after a clean stop.
                    listener.progress("Updating the head service / STOP active control first...");
                    exec(session,NaoRuntime.run(runtime,manager+" stop"));
                }
                {
                    listener.progress("Installing the head service / motors stay stopped...");
                    try{sftp.mkdir(ROOT);}catch(SftpException exists){sftp.stat(ROOT);}
                    for(String name:activity.getAssets().list("nao"))if(name.endsWith(".py")){
                        try(InputStream in=activity.getAssets().open("nao/"+name)){sftp.put(in,ROOT+"/"+name);try{sftp.rm(ROOT+"/"+name+"c");}catch(SftpException missingCache){}}
                    }
                    if(!installed){byte[] bytes=new byte[24];new SecureRandom().nextBytes(bytes);StringBuilder text=new StringBuilder();for(byte b:bytes)text.append(String.format("%02x",b&255));pairing=text.toString();}
                    sftp.put(new ByteArrayInputStream(pairing.getBytes(StandardCharsets.UTF_8)),ROOT+"/.telenao-token");sftp.chmod(0600,ROOT+"/.telenao-token");
                }
                listener.progress("Starting the head service / tracking stays paused...");
                JSONObject started=new JSONObject(exec(session,NaoRuntime.run(runtime,ROOT+"/manage.py start")));
                if(!started.optBoolean("running",false))throw new IOException("Robot service did not become ready");
                listener.ready(pairing);
            }catch(Exception error){listener.failed(error.getMessage()==null?error.getClass().getSimpleName():error.getMessage());}
            finally{if(sftp!=null)sftp.disconnect();if(session!=null)session.disconnect();}
        },"telenao-owner-connect").start();
    }
}
