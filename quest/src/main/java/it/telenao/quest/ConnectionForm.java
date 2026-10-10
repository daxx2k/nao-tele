package it.telenao.quest;

import android.app.Activity;
import android.view.WindowManager;
import android.widget.*;
import it.telenao.ui.StudioStyle;

/** Compact, fixed connection panel; actions and the VR footer stay visible. */
final class ConnectionForm {
    static TextView label(StudioStyle ui, String value, int size, int color) {
        return ui.text(value, size >= 24 ? 22 : Math.min(size, 14), color, size >= 24);
    }
    static EditText field(StudioStyle ui, LinearLayout parent, String title, String value, boolean secret) {
        EditText edit = ui.field(parent, title, value, secret);
        TextView label = (TextView) parent.getChildAt(parent.getChildCount()-2);
        label.setTextSize(11);
        LinearLayout.LayoutParams space = (LinearLayout.LayoutParams) label.getLayoutParams();
        space.setMargins(0, ui.dp(6), 0, ui.dp(3)); label.setLayoutParams(space);
        edit.setTextSize(16); edit.setPadding(ui.dp(10), ui.dp(4), ui.dp(10), ui.dp(4));
        edit.getLayoutParams().height = ui.dp(38);
        return edit;
    }
    static LinearLayout.LayoutParams buttonSpace(StudioStyle ui){
        LinearLayout.LayoutParams value=new LinearLayout.LayoutParams(-1,ui.dp(40));
        value.setMargins(0,ui.dp(6),0,0);return value;
    }
    static LinearLayout.LayoutParams halfButtonSpace(StudioStyle ui, boolean right){
        LinearLayout.LayoutParams value=new LinearLayout.LayoutParams(0,ui.dp(40),1);
        value.setMargins(right?ui.dp(4):0,ui.dp(6),right?0:ui.dp(4),0);return value;
    }
    static final class Status extends TextView {
        private java.util.ArrayList<String> history=new java.util.ArrayList<>();
        Status(Activity activity,StudioStyle ui){super(activity);setTextSize(14);setTextColor(ui.ink);setTextIsSelectable(true);setPadding(0,ui.dp(6),0,ui.dp(6));}
        @Override public void setText(CharSequence value,BufferType type){
            super.setText(value,type);
            if(history!=null&&value!=null&&!value.toString().isEmpty()&&(history.isEmpty()||!history.get(history.size()-1).equals(value.toString()))){history.add(value.toString());if(history.size()>32)history.remove(0);}
        }
        void showHistory(){
            TextView content=new TextView(getContext());content.setTextSize(14);content.setTextIsSelectable(true);content.setPadding(24,16,24,16);content.setText(android.text.TextUtils.join("\n\n",history));
            ScrollView scroll=new ScrollView(getContext());scroll.addView(content);
            new android.app.AlertDialog.Builder(getContext()).setTitle("Connection log").setView(scroll).setPositiveButton("Close",null).show();
        }
    }
    static void show(Activity activity, StudioStyle ui, LinearLayout root, Button enter) {
        enter.setTextSize(15);enter.setText("Open VR");
        LinearLayout.LayoutParams footer=new LinearLayout.LayoutParams(-1,ui.dp(48));
        footer.setMargins(0,ui.dp(10),0,0);root.addView(enter,footer);
        activity.getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE
                | WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        activity.setContentView(root);
    }
}
