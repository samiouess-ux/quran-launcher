const $ = (id) => document.getElementById(id);
const canvas = $("stage"), ctx = canvas.getContext("2d"), W = canvas.width, H = canvas.height;
let audioUrl = null, imageUrl = null, backgroundImage = null, audioElement = null, audioContext = null, audioSource = null;
let currentAyahs = [], selectedSurahName = "";
const surahNames = ["الفاتحة","البقرة","آل عمران","النساء","المائدة","الأنعام","الأعراف","الأنفال","التوبة","يونس","هود","يوسف","الرعد","إبراهيم","الحجر","النحل","الإسراء","الكهف","مريم","طه","الأنبياء","الحج","المؤمنون","النور","الفرقان","الشعراء","النمل","القصص","العنكبوت","الروم","لقمان","السجدة","الأحزاب","سبأ","فاطر","يس","الصافات","ص","الزمر","غافر","فصلت","الشورى","الزخرف","الدخان","الجاثية","الأحقاف","محمد","الفتح","الحجرات","ق","الذاريات","الطور","النجم","القمر","الرحمن","الواقعة","الحديد","المجادلة","الحشر","الممتحنة","الصف","الجمعة","المنافقون","التغابن","الطلاق","التحريم","الملك","القلم","الحاقة","المعارج","نوح","الجن","المزمل","المدثر","القيامة","الإنسان","المرسلات","النبأ","النازعات","عبس","التكوير","الانفطار","المطففين","الانشقاق","البروج","الطارق","الأعلى","الغاشية","الفجر","البلد","الشمس","الليل","الضحى","الشرح","التين","العلق","القدر","البينة","الزلزلة","العاديات","القارعة","التكاثر","العصر","الهمزة","الفيل","قريش","الماعون","الكوثر","الكافرون","النصر","المسد","الإخلاص","الفلق","الناس"];
function wrapArabic(text,maxWidth,font){ctx.font=font;const words=text.trim().split(/\s+/);const lines=[];let line="";for(const word of words){const test=line?line+" "+word:word;if(ctx.measureText(test).width>maxWidth&&line){lines.push(line);line=word;}else line=test;}if(line)lines.push(line);return lines;}
function draw(){
 ctx.clearRect(0,0,W,H);
 if(backgroundImage){const scale=Math.max(W/backgroundImage.width,H/backgroundImage.height),iw=backgroundImage.width*scale,ih=backgroundImage.height*scale;ctx.drawImage(backgroundImage,(W-iw)/2,(H-ih)/2,iw,ih);}
 else{const g=ctx.createLinearGradient(0,0,W,H);g.addColorStop(0,"#183d30");g.addColorStop(.55,"#10251e");g.addColorStop(1,"#07120e");ctx.fillStyle=g;ctx.fillRect(0,0,W,H);for(let i=0;i<18;i++){ctx.beginPath();ctx.arc((i*173)%W,(i*97)%H,2+(i%4),0,Math.PI*2);ctx.fillStyle="rgba(216,182,106,.18)";ctx.fill();}}
 ctx.fillStyle="rgba(4,12,9,.58)";ctx.fillRect(0,0,W,H);ctx.strokeStyle="rgba(216,182,106,.75)";ctx.lineWidth=3;ctx.strokeRect(35,35,W-70,H-70);ctx.textAlign="center";ctx.direction="rtl";
 ctx.fillStyle="#e0c47f";ctx.font="700 30px Cairo, sans-serif";ctx.fillText(selectedSurahName||"القرآن الكريم",W/2,125);
 ctx.fillStyle="#fff9e9";const verse=$("ayah").value.trim()||"بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ";let fontSize=54,lines=wrapArabic(verse,W-190,"700 "+fontSize+"px Amiri, serif");while(lines.length>4&&fontSize>34){fontSize-=4;lines=wrapArabic(verse,W-190,"700 "+fontSize+"px Amiri, serif");}
 ctx.font="700 "+fontSize+"px Amiri, serif";const lineHeight=fontSize*1.65,startY=H/2-((lines.length-1)*lineHeight)/2;lines.forEach((line,i)=>ctx.fillText(line,W/2,startY+i*lineHeight,W-150));
 ctx.fillStyle="#d8b66a";ctx.font="600 22px Cairo, sans-serif";ctx.fillText($("reciter").value.trim(),W/2,H-105);ctx.fillStyle="rgba(255,255,255,.65)";ctx.font="18px Cairo, sans-serif";ctx.fillText("صدقة جارية",W/2,H-65);
}
["reciter"].forEach(id=>$(id).addEventListener("input",draw));$("preview").addEventListener("click",draw);
$("background").addEventListener("change",e=>{const file=e.target.files[0];if(!file)return;if(imageUrl)URL.revokeObjectURL(imageUrl);imageUrl=URL.createObjectURL(file);backgroundImage=new Image();backgroundImage.onload=draw;backgroundImage.onerror=()=>$("status").textContent="تعذّر فتح الصورة المختارة.";backgroundImage.src=imageUrl;$("imageName").textContent=file.name;});
$("audio").addEventListener("change",e=>{const file=e.target.files[0];if(!file)return;if(audioUrl)URL.revokeObjectURL(audioUrl);audioUrl=URL.createObjectURL(file);$("audioName").textContent=file.name;$("status").textContent="تم اختيار التلاوة. اضغط «إنشاء الفيديو».";});
$("render").addEventListener("click",async()=>{
 const file=$("audio").files[0];if(!file){$("status").textContent="من فضلك اختر ملف التلاوة الصوتية أولاً.";return;}
 if(!window.MediaRecorder||!canvas.captureStream){$("status").textContent="المتصفح لا يدعم تسجيل الفيديو. جرّب Chrome أو Safari محدّثاً.";return;}
 const button=$("render");button.disabled=true;$("download").classList.add("disabled");$("download").removeAttribute("href");$("status").textContent="جارٍ تجهيز الفيديو...";
 let canvasStream=null,destination=null,recorder=null;
 try{
  if(audioElement){audioElement.pause();audioElement.removeAttribute("src");}
  audioElement=new Audio(audioUrl);audioElement.preload="auto";const AudioCtx=window.AudioContext||window.webkitAudioContext;if(!AudioCtx)throw new Error("المتصفح لا يدعم تشغيل الصوت داخل التسجيل.");
  if(!audioContext){audioContext=new AudioCtx();audioSource=audioContext.createMediaElementSource(audioElement);}
  destination=audioContext.createMediaStreamDestination();audioSource.connect(destination);await audioContext.resume();
draw();canvasStream=canvas.captureStream(30);
  const stream=new MediaStream([...canvasStream.getVideoTracks(),...destination.stream.getAudioTracks()]);
  const mime=["video/webm;codecs=vp9,opus","video/webm;codecs=vp8,opus","video/webm"].find(t=>MediaRecorder.isTypeSupported(t));recorder=new MediaRecorder(stream,mime?{mimeType:mime}:undefined);const chunks=[];
  recorder.ondataavailable=e=>{if(e.data&&e.data.size)chunks.push(e.data);};
  recorder.onerror=()=>{$("status").textContent="حدث خطأ أثناء تسجيل الفيديو.";button.disabled=false;canvasStream.getTracks().forEach(t=>t.stop());destination.stream.getTracks().forEach(t=>t.stop());};
  recorder.onstop=()=>{const blob=new Blob(chunks,{type:recorder.mimeType||"video/webm"});if(!blob.size){$("status").textContent="لم يتم إنشاء ملف الفيديو. حاول مجدداً.";button.disabled=false;return;}const url=URL.createObjectURL(blob);$("download").href=url;$("download").download="quran-video.webm";$("download").classList.remove("disabled");$("download").setAttribute("aria-disabled","false");$("download").textContent="تحميل الفيديو ("+(blob.size/1024/1024).toFixed(1)+" MB)";$("status").textContent="اكتمل إنشاء الفيديو! اضغط تحميل الفيديو لحفظه.";button.disabled=false;canvasStream.getTracks().forEach(t=>t.stop());destination.stream.getTracks().forEach(t=>t.stop());};
  recorder.start(250);$("status").textContent="جارٍ تسجيل الفيديو مع التلاوة...";audioElement.onended=()=>{if(recorder.state!=="inactive")recorder.stop();};audioElement.onerror=()=>{if(recorder.state!=="inactive")recorder.stop();$("status").textContent="تعذّر قراءة ملف الصوت. جرّب MP3 أو WAV.";};await audioElement.play();
 }catch(err){$("status").textContent=err.message||"تعذّر إنشاء الفيديو. تحقق من صلاحية تشغيل الصوت.";button.disabled=false;if(canvasStream)canvasStream.getTracks().forEach(t=>t.stop());if(destination)destination.stream.getTracks().forEach(t=>t.stop());}
});
surahNames.forEach((name,i)=>{const option=document.createElement("option");option.value=String(i+1);option.textContent=(i+1)+" — "+name;$("surahSelect").appendChild(option);});
async function loadSurah(number){
 if(!number)return;
 selectedSurahName="سورة "+surahNames[Number(number)-1];$("surahInfo").textContent="جارٍ تحميل آيات "+selectedSurahName+"...";
 $("ayah").value="جارٍ تحميل الآيات...";
 try{
  const response=await fetch("https://api.alquran.cloud/v1/surah/"+number+"/quran-uthmani");
  if(!response.ok)throw new Error("network");
  const result=await response.json();if(result.code!==200)throw new Error("api");
  currentAyahs=result.data.ayahs;$("ayahFrom").value=1;$("ayahTo").value=currentAyahs.length;
  $("ayahFrom").max=currentAyahs.length;$("ayahTo").max=currentAyahs.length;updateAyahRange();
  $("status").textContent="تم تحميل السورة. اختر نطاق الآيات وملف التلاوة.";
 }catch(error){currentAyahs=[];$("ayah").value="تعذّر تحميل الآيات. تحقق من اتصال الإنترنت وأعد اختيار السورة.";$("surahInfo").textContent="فشل تحميل نص السورة.";$("status").textContent="تعذّر جلب نص القرآن من المصدر.";}
}
function updateAyahRange(){
 if(!currentAyahs.length)return;
 let from=Math.max(1,Number($("ayahFrom").value)||1),to=Math.max(from,Number($("ayahTo").value)||from);
 from=Math.min(from,currentAyahs.length);to=Math.min(to,currentAyahs.length);
 $("ayahFrom").value=from;$("ayahTo").value=to;
 $("ayah").value=currentAyahs.slice(from-1,to).map(item=>item.text).join(" ۞ ");
 $("surahInfo").textContent="عدد آيات السورة: "+currentAyahs.length+" — الآيات المختارة: "+from+" إلى "+to;
 draw();
}
$("surahSelect").addEventListener("change",event=>loadSurah(event.target.value));
["ayahFrom","ayahTo"].forEach(id=>$(id).addEventListener("change",updateAyahRange));

draw();