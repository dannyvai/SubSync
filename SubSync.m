clc
clear all
close all
addpath('jsonlab-1.5');
path=pwd;

%% Input Files
srt='friends.s03e07.720p.bluray.x264-psychd';
video='friends.s03e07.720p.bluray.sujaidr.mkv';
vid_length=22*60+47;

% srt='S01E05';
% video='S01E05.mkv';
% vid_length=21*60+11;

% srt='rick.and.morty.s01e05.720p.hdtv.x264-2hd';
% video='S01E05.mkv';
% vid_length=21*60+11;

% srt='Rick.and.Morty.s01e07.hdtv.x264-2hd.eng';
% video='S01E07.mkv';
% vid_length=22*60;

%% Algorithm Parameters
credits_length=30;
intro_length=30;
dur=60;
win=5;
num_of_seg=15;
max_dist=0.3;
min_words=5;
shift_w=0.1;

vid_length=vid_length-credits_length;
t_off_vect=floor(linspace(intro_length,vid_length-dur,num_of_seg));

%% Create BAT Files
cd work
for i_s=1 : 1 : num_of_seg
    i_s
    t_off=t_off_vect(i_s);
    json{i_s}=[video,'_dur_',num2str(dur),'_seg_',num2str(i_s),'_of_',num2str(num_of_seg)];
    
    t_off_h=floor(t_off/3600);
    t_off_m=floor((t_off-t_off_h*3600)/60);
    t_off_s=floor(t_off-t_off_h*3600-t_off_m*60);
    
    dur_h=floor(dur/3600);
    dur_m=floor((dur-dur_h*3600)/60);
    dur_s=floor(dur-dur_h*3600-dur_m*60);
    
    fid=fopen(['Speech2Text_',num2str(i_s),'_of_',num2str(num_of_seg),'.bat'],'w');
    fprintf(fid,['ffmpeg -i ..\\videos\\',video,' -ss ',num2str(t_off_h),':',num2str(t_off_m),':',num2str(t_off_s),' -t ',num2str(dur_h),':',num2str(dur_m),':',num2str(dur_s),' -vn -acodec libvorbis -y seg_',num2str(i_s),'_of_',num2str(num_of_seg),'.ogg\n']);
    fprintf(fid,['curl -X POST -u 31f5a1c6-e2de-4f2a-bc11-2b7c9333729e:AfQb1VnVq57R --header "Content-Type: audio/ogg;codecs=vorbis" --header "Transfer-Encoding: chunked" --data-binary @seg_',num2str(i_s),'_of_',num2str(num_of_seg),'.ogg "https://stream.watsonplatform.net/speech-to-text/api/v1/recognize?continuous=true&timestamps=true&max_alternatives=1" > ',json{i_s},'_pre.txt\n']);
    fprintf(fid,['rename ',json{i_s},'_pre.txt ',json{i_s},'.txt\n']);
    fprintf(fid,'exit');
    fclose(fid);
end

%% Run Speech2Text
for i_s=1 : 1 : num_of_seg
    if ~exist(['work\',json{i_s},'.txt'], 'file')
        system(['Speech2Text_',num2str(i_s),'_of_',num2str(num_of_seg),'.bat &']);
    end
end
cd ..

disp('Waiting for outputs...');
counter=0;
while 1
    for i_s=1 : 1 : num_of_seg
        if exist(['work\',json{i_s},'.txt'], 'file')
            counter=counter+1;
        end
    end
    if counter==num_of_seg
        clc
        break;
    end
    counter=0;
end

%% Read Subtitles
fid=fopen(['subtitles\',srt,'.srt'],'r');
while ~feof(fid)
    l=fgetl(fid);
    ind=str2double(l);
    times=fgetl(fid);
    t1=times(1:12);
    th=str2double(t1(1:2));
    tm=str2double(t1(4:5));
    ts=str2double(t1(7:8))+str2double(t1(10:12))/1000;
    t_start(ind)=th*3600+tm*60+ts;
    t2=times(18:end);
    th=str2double(t2(1:2));
    tm=str2double(t2(4:5));
    ts=str2double(t2(7:8))+str2double(t2(10:12))/1000;
    t_end(ind)=th*3600+tm*60+ts;
    
    k=1;
    while 1
        l=fgetl(fid);
        if k==1
            text_orig{ind}=l;
        else
            text_orig{ind}=[text_orig{ind},'\r\n ',l];
        end
        l=strtrim(l);
        if isempty(l)
            break;
        end
        txt=strsplit(l);
        str = regexprep(txt(1),'[,\.><!\?]','');      %# Remove characters using regexprep
        if k==1
            text{ind}=str;
        end
        k=k+1;
    end
end
fclose(fid);

%% Compare Words
j_s=1;
for i_s=1 : 1 : num_of_seg
    i_s
    t_off=t_off_vect(i_s);
    json_txt=fileread(['work\',json{i_s},'.txt']);
    data = loadjson(json_txt);
    if ~isfield(data,'results')
        diff{i_s}=NaN;
        continue;
    end
    k=1;
    for ir=1 : 1 : length(data.results);
        dat=data.results{ir}.alternatives{1};
        for i=1 :1 : length(dat.timestamps)
            word=dat.timestamps{i}{1};
            %             if strcmpi(word,'i') || strcmpi(word,'you') || strcmpi(word,'are') || strcmpi(word,'is') || strcmpi(word,'the') || strcmpi(word,'a') || strcmp(word,'%HESITATION')
            %                 continue;
            %             end
            %             if strcmpi(word,'it') || strcmpi(word,'we') || strcmpi(word,'i') || strcmpi(word,'you') || strcmpi(word,'are') || strcmpi(word,'is') || strcmpi(word,'the') || strcmpi(word,'a') || strcmpi(word,'and') || strcmpi(word,'to') || strcmp(word,'%HESITATION')
            %                 continue;
            %             end
            if ~isempty(word)
                t_ws=t_off+dat.timestamps{i}{2};
                found=0;
                if j_s>1
                    t_g=t_ws+dm(j_s-1);
                    i_g=find(t_start>=t_g,1,'first');
                    for j=i_g-1 : 1 : i_g+1
                        word_srt=text{j};
                        if strcmpi(word_srt,word)
                            t_ws_vid(k)=t_ws;
                            t_ws_srt(k)=t_start(j);
                            words{k}=word;
                            k=k+1;
                            found=1;
                            break;
                        end
                    end
                    if ~found
                        t_min=t_ws-win;
                        t_max=t_ws+win;
                        i_min=find(t_start>t_min,1,'first');
                        i_max=find(t_start<t_max,1,'last');
                        for j=i_min : 1 : i_max
                            word_srt=text{j};
                            if strcmpi(word_srt,word)
                                t_ws_vid(k)=t_ws;
                                t_ws_srt(k)=t_start(j);
                                words{k}=word;
                                k=k+1;
                                break;
                            end
                        end
                    end
                else
                    t_min=t_ws-win;
                    t_max=t_ws+win;
                    i_min=find(t_start>t_min,1,'first');
                    i_max=find(t_start<t_max,1,'last');
                    for j=i_min : 1 : i_max
                        word_srt=text{j};
                        if strcmpi(word_srt,word)
                            t_ws_vid(k)=t_ws;
                            t_ws_srt(k)=t_start(j);
                            words{k}=word;
                            k=k+1;
                            break;
                        end
                    end
                end
            end
        end
    end
    
    [t_ws_srt,iu]=unique(t_ws_srt);
    words=words(iu);
    t_ws_vid=t_ws_vid(iu);
    
    if ~exist('words','var')
        diff{i_s}=NaN;
    elseif length(words)<min_words
        diff{i_s}=NaN;
    else
        words
        t_ws_vid
        t_ws_srt
        diff_temp=t_ws_vid-t_ws_srt;
        diff_m=median(diff_temp);
        dist=diff_temp-diff_m;
        i_ok=find(abs(dist)<max_dist);
        diff_temp=diff_temp(i_ok);
        if length(diff_temp)<min_words
            diff{i_s}=NaN;
        else
            diff{i_s}=diff_temp;
            dm(j_s)=mean(diff{i_s});
            dt(j_s)=t_off_vect(i_s)+dur/2;
            j_s=j_s+1;
        end
    end
    clear t_ws_vid t_ws_srt words
end
%% Calculate Subtitles Shift
for i=1 :1 : ind(end)
    ts=t_start(i);
    te=t_end(i);
    if ts<dt(1)
        shift=dm(1)-shift_w;
    elseif ts>dt(end)
        shift=dm(end)-shift_w;
    else
        shift=interp1(dt,dm,ts)-shift_w;
    end
    if ~isnan(shift)
        t_start(i)=t_start(i)+shift;
        t_end(i)=t_end(i)+shift;
    end
end
%% Write Subtitles
fid=fopen(['subtitles\',srt,'_shifted.srt'],'w');
for i=1 :1 : ind(end)
    ts=t_start(i);
    te=t_end(i);
    
    ts_h=floor(ts/3600);
    ts_m=floor((ts-ts_h*3600)/60);
    ts_s=floor(ts-ts_h*3600-ts_m*60);
    ts_ms=floor((ts-ts_h*3600-ts_m*60-ts_s)*1000);
    
    te_h=floor(te/3600);
    te_m=floor((te-te_h*3600)/60);
    te_s=floor(te-te_h*3600-te_m*60);
    te_ms=floor((te-te_h*3600-te_m*60-te_s)*1000);
    
    if ts_m>9
        ts_m_str=num2str(ts_m);
    else
        ts_m_str=['0',num2str(ts_m)];
    end
    
    if ts_s>9
        ts_s_str=num2str(ts_s);
    else
        ts_s_str=['0',num2str(ts_s)];
    end
    
    if ts_ms>99
        ts_ms_str=num2str(ts_ms);
    elseif ts_ms>9
        ts_ms_str=['0',num2str(ts_ms)];
    else
        ts_ms_str=['00',num2str(ts_ms)];
    end
    
    if te_m>9
        te_m_str=num2str(te_m);
    else
        te_m_str=['0',num2str(te_m)];
    end
    
    if te_s>9
        te_s_str=num2str(te_s);
    else
        te_s_str=['0',num2str(te_s)];
    end
    
    if te_ms>99
        te_ms_str=num2str(te_ms);
    elseif te_ms>9
        te_ms_str=['0',num2str(te_ms)];
    else
        te_ms_str=['00',num2str(te_ms)];
    end
    
    time_str=['0',num2str(ts_h),':',ts_m_str,':',ts_s_str,',',ts_ms_str,' --> 0',num2str(te_h),':',te_m_str,':',te_s_str,',',te_ms_str,'\r\n'];
    
    if i==1
        time_str0=['00:00:00,000 --> ',time_str(1:12),'\r\n'];
        fprintf(fid,'%d\r\n',i);
        fprintf(fid,time_str0);
        fprintf(fid,'Created Using SubSync. PLEASE DONATE!\r\n');
        fprintf(fid,'\n');
    end
    
    fprintf(fid,'%d\r\n',i+1);
    fprintf(fid,time_str);
    fprintf(fid,[text_orig{i},'\r\n']);
    fprintf(fid,'\r\n');
end
fclose(fid);

%% Plot Outputs
% figure
% hold on
% col='rkbcmrkbcmrkbcmrkbcmrkbcmrkbcmrkbcmrkbcmrkbcmrkbcmrkbcmrkbcm';
% max_l=0;
% j=1;
% for i=1 :1 : num_of_seg
%     if ~isnan(diff{i})
%         diff_l=length(diff{i});
%         if diff_l>max_l
%             max_l=diff_l;
%         end
%         plot(diff{i},'o','color',col(i));
%         plot([1 100],[dm(j),dm(j)],'--','color',col(i),'linewidth',2);
%         j=j+1;
%     end
% end
% grid on
% xlim([1 max_l]);

figure
plot(dt/60,dm,'-o','linewidth',2)
grid on
% ylim([-2 2]);

% figure
% plot(dt/60,ds,'-o','linewidth',2)
% grid on