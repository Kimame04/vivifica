function redirect(name){
  var ele = document.getElementById(name)
  ele.scrollIntoView()
}

function SmoothVerticalScrolling(e, time, where) {
  var eTop = e.getBoundingClientRect().top;
  var eAmt = eTop / 100;
  var curTime = 0;
  while (curTime <= time) {
      window.setTimeout(SVS_B, curTime, eAmt, where);
      curTime += time / 100;
  }
}

function SVS_B(eAmt, where) {
  if(where == "center" || where == "")
      window.scrollBy(0, eAmt / 2);
  if (where == "top")
      window.scrollBy(0, eAmt);
}

function search(id1, id2, id3, id4, id5){
  var new_tbody = document.createElement('tbody');
  new_tbody.id = 'results'

  var old_tbody = document.getElementById(id4)
  old_tbody.hidden = false

  var table = document.getElementById(id5)
  table.deleteTHead()
  var header = table.createTHead()
  var row = header.insertRow(0);
  var th1 = row.insertCell(0);
  var th2 = row.insertCell(1)
  var th3 = row.insertCell(2)

  th1.innerHTML = "<p>Date"
  th2.innerHTML = "<p>Aircraft"
  th3.innerHTML = "<p>Service Type"


  var entry;
  for (var j = 0; j < 4; j++) {
      entry = {
          date: id1.value + j,
          aircraft: id2.value + j,
          service: id3.value + j,
      };
      var row = new_tbody.insertRow(-1);
      var cell1 = row.insertCell(0);
      var cell2 = row.insertCell(1);
      var cell3 = row.insertCell(2);

      cell1.innerHTML = "<p>" + entry.date,
      cell2.innerHTML = "<p>" + entry.aircraft,
      cell3.innerHTML = "<p>" + entry.service;
      console.log(entry.date)
  }

  table.replaceChild(new_tbody, old_tbody)


}

