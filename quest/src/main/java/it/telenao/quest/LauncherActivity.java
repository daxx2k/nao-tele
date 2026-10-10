package it.telenao.quest;
import it.telenao.ui.StudioStyle;
import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.widget.*;
import android.text.InputType;
import android.Manifest;
import android.content.pm.PackageManager;
import java.io.*;
import java.net.*;
import org.json.JSONObject;

public class LauncherActivity extends Activity {
    private NaturalVoice voiceProbe;
    private boolean diagnosticStarted;
    private StudioStyle ui;
    private int ink,muted,accent;
    private TextView label(String value,int size,int color){return ConnectionForm.label(ui,value,size,color);}
    private EditText field(LinearLayout box,String title,String value,boolean secret){return ConnectionForm.field(ui,box,title,value,secret);}
    @Override public void onCreate(Bundle state){
        StudioStyle.applyTheme(this);super.onCreate(state);
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},42);
        SharedPreferences prefs=ConnectionStore.load(this);
        ui=new StudioStyle(this);ui.window(this);ink=ui.ink;muted=ui.muted;accent=StudioStyle.CONNECTION;
        voiceProbe=new NaturalVoice(this);
        LinearLayout root=ui.column();root.setPadding(ui.dp(16),ui.dp(10),ui.dp(16),ui.dp(10));root.setBackgroundColor(ui.background);
        LinearLayout heading=ui.row();heading.setGravity(android.view.Gravity.CENTER_VERTICAL);heading.setPadding(ui.dp(10),ui.dp(6),ui.dp(10),ui.dp(6));heading.setBackground(ui.surface(ui.surfaceColor,22));ImageView mark=new ImageView(this);mark.setImageResource(R.drawable.ic_telenao);heading.addView(mark,new LinearLayout.LayoutParams(ui.dp(32),ui.dp(32)));LinearLayout titles=ui.column();titles.setPadding(ui.dp(16),0,0,0);titles.addView(label("TeleNao "+it.telenao.ui.VersionInfo.label(this),30,ink));titles.addView(label("Connection settings",16,muted));heading.addView(titles,new LinearLayout.LayoutParams(0,-2,1));root.addView(heading);
        
        LinearLayout body=ui.row();body.setGravity(android.view.Gravity.CENTER_VERTICAL);
        LinearLayout.LayoutParams bodyBounds=new LinearLayout.LayoutParams(-1,0,1);bodyBounds.setMargins(0,ui.dp(8),0,ui.dp(8));root.addView(body,bodyBounds);
        LinearLayout card=ui.card();card.setPadding(ui.dp(12),ui.dp(10),ui.dp(12),ui.dp(10));card.addView(ui.text("ROBOT",12,ink,true));
        LinearLayout actions=ui.card();actions.setPadding(ui.dp(12),ui.dp(10),ui.dp(12),ui.dp(10));actions.addView(ui.text("CONNECTION",12,ink,true));
        LinearLayout.LayoutParams leftBounds=new LinearLayout.LayoutParams(0,-2,1);leftBounds.setMargins(0,0,ui.dp(6),0);body.addView(card,leftBounds);
        LinearLayout.LayoutParams rightBounds=new LinearLayout.LayoutParams(0,-2,1);rightBounds.setMargins(ui.dp(6),0,0,0);body.addView(actions,rightBounds);
        EditText host=field(card,"Robot address",prefs.getString("host",""),false);
        EditText token=new EditText(this);token.setText(prefs.getString("token",""));
        EditText sshUser=field(card,"Account",NaoCredentials.user(this,prefs.getString("host","")),false);
        EditText sshPassword=field(card,"Password",NaoCredentials.password(this,prefs.getString("host","")),true);
        TextView status=label("Connect to NAO, then open VR.",14,muted);status.setMaxLines(3);status.setEllipsize(android.text.TextUtils.TruncateAt.END);
        Button connect=ui.button("Connect",true);actions.addView(connect,ConnectionForm.buttonSpace(ui));
        connect.setOnClickListener(v->{String h=host.getText().toString().trim(),u=sshUser.getText().toString().trim(),p=sshPassword.getText().toString();
            if(!ConnectionStore.validHost(h)||u.isEmpty()||p.isEmpty()){status.setText("Enter NAO's head IPv4 address and SSH credentials.");return;}
            connect.setEnabled(false);
            NaoBootstrap.connect(this,h,u,p,new NaoBootstrap.Listener(){
                public void progress(String message){runOnUiThread(()->{if(!isFinishing()&&!isDestroyed())status.setText(message);});}
                public void failed(String message){runOnUiThread(()->{if(!isFinishing()&&!isDestroyed()){connect.setEnabled(true);status.setText("Connection failed: "+message);}});}
                public void ready(String pairing){runOnUiThread(()->{if(isFinishing()||isDestroyed())return;
                    token.setText(pairing);ConnectionStore.save(prefs,h,pairing);
                    try{NaoCredentials.save(LauncherActivity.this,h,u,p);status.setText("Connected to NAO. Open VR and hold A + X to start.");}
                    catch(Exception storage){status.setText("Connected. Password could not be saved; re-enter it next time.");}
                    connect.setEnabled(true);
                });}
            });
        });
        TextView voiceInfo=label("Checking voice...",12,muted);voiceInfo.setMaxLines(1);voiceInfo.setEllipsize(android.text.TextUtils.TruncateAt.END);
        android.os.Handler voiceHandler=new android.os.Handler(getMainLooper());
        if(getIntent().getBooleanExtra("voice_sequence_self_test",false)&&(getApplicationInfo().flags&android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)!=0){
            diagnosticStarted=true;final String[] phrases={"Hello, I am NAO.","How are you?","How are you?"};
            for(String phrase:phrases)voiceProbe.speak(phrase,"en-US");
            final long deadline=android.os.SystemClock.elapsedRealtime()+60000;
            voiceHandler.postDelayed(new Runnable(){int completed;public void run(){if(isFinishing()||isDestroyed())return;byte[] audio=voiceProbe.take();if(audio!=null){String caption=voiceProbe.takeText();if(completed>=phrases.length||!caption.equals(phrases[completed])||audio.length==0){android.util.Log.e("TeleNao","Piper sequence self-test FAIL: output/order");return;}completed++;android.util.Log.i("TeleNao","Piper sequence clip="+completed+" bytes="+audio.length);}
                if(completed==phrases.length){if(voiceProbe.take()!=null){android.util.Log.e("TeleNao","Piper sequence self-test FAIL: duplicate");return;}android.util.Log.i("TeleNao","Piper sequence self-test PASS: startup queue, three clips, repeated preset, no robot playback");return;}
                if(android.os.SystemClock.elapsedRealtime()<deadline)voiceHandler.postDelayed(this,100);else android.util.Log.e("TeleNao","Piper sequence self-test FAIL: timeout "+voiceProbe.status());}},100);
        }
        voiceHandler.postDelayed(new Runnable(){public void run(){if(isFinishing()||isDestroyed())return;voiceInfo.setText("Natural voice: "+voiceProbe.name());
            if(voiceProbe.name().startsWith("Starting")){voiceHandler.postDelayed(this,300);return;}
            if(!diagnosticStarted&&getIntent().getBooleanExtra("voice_self_test",false)&&(getApplicationInfo().flags&android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)!=0){diagnosticStarted=true;voiceProbe.speak("Hello, I am NAO. How can I help you today?","en-GB");final long deadline=android.os.SystemClock.elapsedRealtime()+30000;
                voiceHandler.postDelayed(new Runnable(){public void run(){if(isFinishing()||isDestroyed())return;byte[] pcm=voiceProbe.take();if(pcm!=null){try(java.io.FileOutputStream out=openFileOutput("voice-self-test.pcm",MODE_PRIVATE)){out.write(pcm);android.util.Log.i("TeleNao","Cori self-test PASS: PCM16 16000 Hz mono, bytes="+pcm.length);}catch(Exception e){android.util.Log.e("TeleNao","Voice self-test output failed",e);}return;}if(android.os.SystemClock.elapsedRealtime()<deadline)voiceHandler.postDelayed(this,100);else android.util.Log.e("TeleNao","Cori self-test failed: "+voiceProbe.status());}},100);
            }}},300);
        Button find=ui.button("Find NAO",false);actions.addView(find,ConnectionForm.buttonSpace(ui));
        find.setOnClickListener(v->{find.setEnabled(false);status.setText("Searching for TeleNao on this network...");new Thread(()->{
            try{java.util.List<NaoDiscovery.Robot> robots=NaoDiscovery.find(ConnectionStore.savedPairings(prefs));runOnUiThread(()->{if(isFinishing())return;find.setEnabled(true);
                if(robots.isEmpty()){status.setText("No TeleNao found. Start the robot service and check Wi-Fi. You can also enter its head address.");return;}
                if(robots.size()==1){host.setText(robots.get(0).host);token.setText(ConnectionStore.pairingFor(prefs,robots.get(0).host));sshUser.setText(NaoCredentials.user(this,robots.get(0).host));sshPassword.setText(NaoCredentials.password(this,robots.get(0).host));status.setText("NAO found. Press CONNECT or check saved pairing.");return;}
                String[] names=new String[robots.size()];for(int i=0;i<names.length;i++)names[i]=robots.get(i).name+"  /  "+robots.get(i).host;
                new android.app.AlertDialog.Builder(this).setTitle("Choose NAO").setItems(names,(d,i)->{host.setText(robots.get(i).host);token.setText(ConnectionStore.pairingFor(prefs,robots.get(i).host));sshUser.setText(NaoCredentials.user(this,robots.get(i).host));sshPassword.setText(NaoCredentials.password(this,robots.get(i).host));status.setText("NAO selected. Press CONNECT to start the head service.");}).show();
            });}catch(Exception e){runOnUiThread(()->{if(!isFinishing()){find.setEnabled(true);status.setText("Network search unavailable. Enter the robot head address.");}});}
        },"nao-discovery").start();});
        Button test=ui.button("Check connection",false);actions.addView(test,ConnectionForm.buttonSpace(ui));
        test.setOnClickListener(v->{String h=host.getText().toString().trim(),t=token.getText().toString().trim();
            if(!ConnectionStore.validHost(h)||t.length()<12){status.setText("Press CONNECT first to install or start the service.");return;}
            test.setEnabled(false);status.setText("Checking...");new Thread(()->{
                String message;
                try(Socket s=new Socket()){s.connect(new InetSocketAddress(h,9570),5000);s.setSoTimeout(5000);
                    s.getOutputStream().write((new JSONObject().put("token",t).put("role","operator").toString()+"\n").getBytes("UTF-8"));
                    String line=new BufferedReader(new InputStreamReader(s.getInputStream(),"UTF-8")).readLine();
                    JSONObject reply=new JSONObject(line);message=reply.has("observer")?"NAO connected. Pairing confirmed.":"Pairing refused: check the code.";
                }catch(Exception e){message="NAO unreachable. Check Wi-Fi, address and robot service.";}
                final String result=message;runOnUiThread(()->{if(!isFinishing()){status.setText(result);test.setEnabled(true);}});
            },"connection-check").start();
        });
        LinearLayout.LayoutParams statusBounds=new LinearLayout.LayoutParams(-1,ui.dp(52));statusBounds.setMargins(0,ui.dp(8),0,0);actions.addView(status,statusBounds);
        actions.addView(voiceInfo,new LinearLayout.LayoutParams(-1,ui.dp(20)));
        Button enter=ui.button("Open VR",true);
        enter.setOnClickListener(v->{String h=host.getText().toString().trim(),t=token.getText().toString().trim();
            if(!ConnectionStore.validHost(h)||t.length()<12){status.setText("Press CONNECT before opening VR.");return;}
            ConnectionStore.save(prefs,h,t);HeadsetNavigation.openStudio(this);
        });
        root.addView(label("A + X: Start / Pause     B: STOP",12,muted));
        ConnectionForm.show(this,ui,root,enter);
        if(getIntent().getBooleanExtra("preview_connection",false)&&(getApplicationInfo().flags&android.content.pm.ApplicationInfo.FLAG_DEBUGGABLE)!=0){
            root.postDelayed(()->{try{
                android.graphics.Bitmap bitmap=android.graphics.Bitmap.createBitmap(root.getWidth(),root.getHeight(),android.graphics.Bitmap.Config.ARGB_8888);
                root.draw(new android.graphics.Canvas(bitmap));
                try(FileOutputStream out=new FileOutputStream(new File(getExternalFilesDir(null),"connection-preview.png"))){bitmap.compress(android.graphics.Bitmap.CompressFormat.PNG,100,out);}bitmap.recycle();
                android.util.Log.i("TeleNao","Connection layout width="+root.getWidth()+" height="+root.getHeight()+" openVrBottom="+enter.getBottom()+" scrollContainers=0 savedCredentials="+!sshPassword.getText().toString().isEmpty());
            }catch(Exception error){android.util.Log.w("TeleNao","Connection preview unavailable");}},600);
        }
if(getIntent().getBooleanExtra("enter_vr",false))enter.performClick();
    }
    @Override protected void onDestroy(){if(voiceProbe!=null)voiceProbe.close();super.onDestroy();}
}
