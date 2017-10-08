package com.example.thesemicolonguy.camapp;

import android.util.Log;
import android.widget.TextView;


import org.apache.http.NameValuePair;
import org.apache.http.message.BasicNameValuePair;

import java.io.DataOutputStream;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UnsupportedEncodingException;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.List;

/**
 * Created by sarthak on 8/10/17.
 */

public class HttpFileUpload implements Runnable {

    URL connectURL;
    String responseString;
    String Title;
    String fileName;
    String Description;
    byte[ ] dataToServer;
    FileInputStream fileInputStream = null;

    // constructor
    HttpFileUpload(String urlString, String vTitle, String vDesc, String file){
        try{
            connectURL = new URL(urlString);
            Title= vTitle;
            Description = vDesc;
            fileName = file;
        }catch(Exception ex){
            Log.i("HttpFileUpload","URL Malformatted");
        }
    }

    String Send_Now(FileInputStream fStream){
        fileInputStream = fStream;
        return Sending();
    }

    private String getQuery(List<NameValuePair> params) throws UnsupportedEncodingException
    {
        StringBuilder result = new StringBuilder();
        boolean first = true;

        for (NameValuePair pair : params)
        {
            if (first)
                first = false;
            else
                result.append("&");

            result.append(URLEncoder.encode(pair.getName(), "UTF-8"));
            result.append("=");
            result.append(URLEncoder.encode(pair.getValue(), "UTF-8"));
        }

        return result.toString();
    }

    String Sending(){

        System.out.println("file Name is :"+fileName);

        String iFileName = fileName;
        String lineEnd = "\r\n";
        String twoHyphens = "--";
        String boundary = "*****";
        String Tag="fSnd";
        try
        {
            Log.e(Tag,"Starting Http File Sending to URL");

            // Open a HTTP connection to the URL
            HttpURLConnection conn = (HttpURLConnection)connectURL.openConnection();

            // Allow Inputs
            conn.setDoInput(true);

            // Allow Outputs
            conn.setDoOutput(true);

            // Don't use a cached copy.
            conn.setUseCaches(false);

            // Use a post method.
            conn.setRequestMethod("POST");

            List<NameValuePair> params = new ArrayList<NameValuePair>();
            params.add(new BasicNameValuePair("fieldname", "userFile"));


            conn.setRequestProperty("Connection", "Keep-Alive");

//            conn.setRequestProperty("Content-Type", "images/jpeg");

            DataOutputStream dos = new DataOutputStream(conn.getOutputStream());

//            dos.writeBytes(twoHyphens + boundary + lineEnd);
//            dos.writeBytes("Content-Disposition: form-data; name=\"title\""+ lineEnd);
//            dos.writeBytes(lineEnd);
//            dos.writeBytes(Title);
//            dos.writeBytes(lineEnd);
//            dos.writeBytes(twoHyphens + boundary + lineEnd);
//
//            dos.writeBytes("Content-Disposition: form-data; name=\"description\""+ lineEnd);
//            dos.writeBytes(lineEnd);
//            dos.writeBytes(Description);
//            dos.writeBytes(lineEnd);
//            dos.writeBytes(twoHyphens + boundary + lineEnd);
//
//            dos.writeBytes("Content-Disposition: form-data; name=\"uploadedfile\";filename=\"" + iFileName +"\"" + lineEnd);
//            dos.writeBytes(lineEnd);
//
//            Log.e(Tag,"Headers are written");

            // create a buffer of maximum size
            int bytesAvailable = fileInputStream.available();

            int maxBufferSize = 1024;
            int bufferSize = Math.min(bytesAvailable, maxBufferSize);
            byte[ ] buffer = new byte[bufferSize];

            // read file and write it into form...
            int bytesRead = fileInputStream.read(buffer, 0, bufferSize);
//            Log.e("TUCHUTIYAHAI", "heyyyyy   up   " + Integer.toString(bytesRead));
            dos.writeChars(getQuery(params));

            while (bytesRead > 0)
            {
                dos.write(buffer, 0, bufferSize);
                bytesAvailable = fileInputStream.available();
                bufferSize = Math.min(bytesAvailable,maxBufferSize);
                bytesRead = fileInputStream.read(buffer, 0,bufferSize);
//                Log.e("TUCHUTIYAHAI", "heyyyyy   bytes    " + Integer.toString(bytesRead));
//                Log.e("TUCHUTIYAHAI", "heyyyyy   dos    " + Integer.toString(dos.size()));


            }
//            dos.writeBytes(lineEnd);
//            dos.writeBytes(twoHyphens + boundary + twoHyphens + lineEnd);
//            Log.e("FUCKOFF", "chutiya" + Integer.toString(dos.size()));
            // close streams
            fileInputStream.close();

            dos.flush();

            Log.e(Tag,"File Sent, Response: "+String.valueOf(conn.getResponseCode()));

            InputStream is = conn.getInputStream();

            // retrieve the response from server
            int ch;

            StringBuffer b =new StringBuffer();
            while( ( ch = is.read() ) != -1 ){ b.append( (char)ch ); }
            String s=b.toString();
            Log.i("Response",s);

            dos.close();

            if(String.valueOf(conn.getResponseCode()).equals("200"))
            {
                return s;
            }else{
                return null;
            }
        }
        catch (MalformedURLException ex)
        {
            Log.e(Tag, "URL error: " + ex.getMessage(), ex);
        }

        catch (IOException ioe)
        {
            Log.e(Tag, "IO error: " + ioe.getMessage(), ioe);
        }
        return null;
    }



    @Override
    public void run() {
    }

}
