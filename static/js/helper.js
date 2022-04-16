var arr = [];
var dict = {};

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

function addDelivery(){
  var airline = document.getElementById("airline");
  var text = airline.options[airline.selectedIndex].value;
  var date = new Date(document.getElementById('date').value).toISOString().split('T')[0];
  console.log(date)
  var node = document.createElement("li");
  node.classList.add('list-group-item')
  var textnode = document.createTextNode(text + " at " + date);
  node.appendChild(textnode);
  document.getElementById("list").appendChild(node);

  var deliveries = document.getElementById('deliveries');
  deliveries.value += (text + ',' + date + "\n");
}

function addOption(){
  var text = document.getElementById('opt').value
  var node = document.createElement("li");
  node.classList.add('list-group-item')
  node.appendChild(document.createTextNode(text))
  document.getElementById("list_option").appendChild(node);
  var options = document.getElementById('options');
  options.value += (text + '\n');
}


function addPart(table_id, select_id){
  var table = document.getElementById(table_id);
  var part = document.getElementById(select_id);
  var name = part.options[part.selectedIndex].value;
  var id = btoa(name).replaceAll("=",'')
  console.log(id)
  if (arr.includes(id)){
      document.getElementById(id).value ++;
      dict[id] ++
      console.log(dict)
  } else {
      var row = table.insertRow();
      var p_name = row.insertCell();  
      p_name.innerHTML = name;
      arr.push(id);
      dict[id] = 1
      var qty = row.insertCell();
      qty.innerHTML = `
      <button type="button" class="btn btn-info btn-sm" onclick="decrementPart(${id})">
      <i class="fa fa-minus"></i>
      </button>
      <input id=${id} type=number min=1 max=999 value=1 readonly>
      <button type="button" class="btn btn-success btn-sm" onclick="incrementPart(${id})">
      <i class="fa fa-plus"></i>
      </button>
      `
      var btn = row.insertCell();
      btn.innerHTML = `
      <button type="button" class="btn btn-danger btn-sm" onclick="deletePart(${id}, ${table_id})">
      <i class="fa fa-x"></i>
      </button>
      `
  }
}

function deletePart(name, table_id){
  var table = document.getElementById(table_id.id);
  var idx = $('table tr').index(table);
  table.deleteRow(idx);
  arr.splice(idx-1, 1);
  postData(dict)
  delete dict[name.id]
}

function incrementPart(id){
  document.getElementById(id.id).value ++;
  dict[id.id] ++
  console.log(dict)
  postData(dict)
}

function decrementPart(id){
  if (document.getElementById(id.id).value > 1) {
    document.getElementById(id.id).value --;
    dict[id.id] --
    console.log(dict)
    postData(dict)
  }
}

function postData(dict){
  $.ajax({
    url: '/postmethod',
    type: 'POST',
    data: dict,
  });
}

function addOption(table_id, option_id, reg_num_id){
  var table = document.getElementById(table_id)
  var option = document.getElementById(option_id).value
  var reg_num = document.getElementById(reg_num_id).value
  var key = reg_num + option
  var result = {'reg_num': reg_num, 'option': option, 'func': 'add'}
  if (arr.includes(key)){
    alert('Option already exists')
  } else{
    arr.push(key)
    var row = table.insertRow()
    var name_cell = row.insertCell()
    name_cell.innerHTML = option
    var action_cell = row.insertCell()
    action_cell.innerHTML = `
    <button type="button" class="btn btn-danger btn-sm" onclick="deleteOption(this, ${table_id})">
    <i class="fa fa-trash-can"></i>
    </button>
    `
    $.ajax({
      url: 'manageOption',
      type: 'POST',
      data: result,
    })
  }
}

function deleteOption(r, table_id){
  var i = r.parentNode.parentNode.rowIndex
  if (table_id.id){
    document.getElementById(table_id.id).deleteRow(i)
  } else {
    document.getElementById(table_id).deleteRow(i)
  }
  arr.splice(i-1, 1);
  var cells = r.parentNode.parentNode.getElementsByTagName('td')
  var option = cells[0].innerHTML
  var reg_num = cells[1].innerHTML
  var result = {'option': option, 'reg_num': reg_num, 'func': 'delete'}
  $.ajax({
    url: 'manageOption',
    type: 'POST',
    data: result,
  })

}

function addDelivery(table_id, airline_id, date_id, reg_num_id){
  var table = document.getElementById(table_id)
  var airline_name = document.getElementById(airline_id).value
  var delivery_date = document.getElementById(date_id).value
  var reg_num = document.getElementById(reg_num_id).value
  var key = reg_num + airline_name + delivery_date
  var result = {'reg_num': reg_num, 'name': airline_name, 'date': delivery_date, 'type': 'add'}

  if (arr.includes(key)){
    alert('Delivery already exists')
  } else {
    arr.push(key)
    var row = table.insertRow()
    var airline_cell = row.insertCell()
    airline_cell.innerHTML = airline_name
    var date = row.insertCell()
    date.innerHTML = delivery_date
    var action_cell = row.insertCell()
    action_cell.innerHTML = `
    <button type="button" class="btn btn-danger btn-sm" onclick="deleteDelivery(this, ${table_id})">
    <i class="fa fa-trash-can"></i>
    </button>
    `
    $.ajax({
      url: 'manageDelivery',
      type: 'POST',
      data: result,
    })
  }
}

function deleteDelivery(r, table_id){
  var i = r.parentNode.parentNode.rowIndex;
  if (table_id.id){
    document.getElementById(table_id.id).deleteRow(i);
  } else {
    document.getElementById(table_id).deleteRow(i);
  }
  arr.splice(i-1, 1);
  var cells = r.parentNode.parentNode.getElementsByTagName("td");
  var airline_name = cells[0].innerHTML
  var date = cells[1].innerHTML
  var reg_num = cells[2].innerHTML
  var result = {'reg_num': reg_num, 'name': airline_name, 'date': date, 'type': 'delete'}
  $.ajax({
    url: 'manageDelivery',
    type: 'POST',
    data: result,
  })
}

function changeFilterState(r, range_id){
  var slider = document.getElementById(range_id);
  if ($(r).is(':checked')) {
    switchStatus = $(r).is(':checked');
    slider.disabled = false
  }
  else {
      switchStatus = $(r).is(':checked');
      slider.disabled = true
  }
}
