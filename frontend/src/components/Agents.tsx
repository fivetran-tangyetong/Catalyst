import React, {useEffect, useState} from 'react';
import { Table, Button, Loader, Center, Alert, Title } from '@mantine/core';
import {
  listApifyActors, runApifyActor,
  listVapiAssistants, makeVapiCall, scheduleVapiCall, getVapiCallStatus,
  generateArcadeUploadUrl, createArcadeSession
} from '../services/mcpService';

export function Agents() {
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string>();
  const [apify, setApify]     = useState<any[]>([]);
  const [vapi, setVapi]       = useState<any[]>([]);

  useEffect(()=>{
    async function load(){
      try{
        setApify(await listApifyActors());
        setVapi(await listVapiAssistants());
      }catch(e:any){
        setError(e.message);
      }finally{
        setLoading(false);
      }
    }
    load();
  },[]);

  if(loading) return <Center><Loader /></Center>;
  if(error)   return <Alert color="red">{error}</Alert>;

  return (
    <div style={{padding:20}}>
      <Title order={4}>Apify Actors</Title>
      <Table>
        <thead><tr><th>Name</th><th>Run</th></tr></thead>
        <tbody>
          {apify.map(a=>(
            <tr key={a.actorId}>
              <td>{a.name}</td>
              <td>
                <Button size="xs" onClick={()=>runApifyActor(a.actorId,{})}>Run</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      <Title order={4} mt="lg">Vapi Assistants</Title>
      <Table>
        <thead><tr><th>Name</th><th>Call</th></tr></thead>
        <tbody>
          {vapi.map(v=>(
            <tr key={v.id}>
              <td>{v.name}</td>
              <td>
                <Button size="xs" onClick={()=>makeVapiCall(v.id,'15551234567','Hi!')}>Call</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      <Title order={4} mt="lg">Arcade Demo</Title>
      <Button
        onClick={async ()=>{
          const { uploadUrl, uploadId } = await generateArcadeUploadUrl('video/mp4');
          alert(`Upload to: ${uploadUrl}\nThen call createArcadeSession('${uploadId}', 'My Title', [])`);
        }}
      >
        Start Arcade Flow
      </Button>
    </div>
  );
}
