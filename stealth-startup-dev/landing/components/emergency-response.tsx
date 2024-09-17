"use client";

import { useState, useEffect, useRef } from "react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Mic,
  Square,
  Send,
  MapPin,
  Moon,
  Sun,
  AlertTriangle,
} from "lucide-react";
import { useCompletion } from "ai/react";
import { cn } from "@/lib/utils";
import Map, { Marker } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import whisper from 'whisper-node';

const MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoicmFqYW5hZ2Fyd2FsIiwiYSI6ImNsZ3U5aDlpaDB1aWUzanA1dzduZWg5b3QifQ.XJMZyFbKT4MjvxsUR8P93g";

export default function EmergencyResponse() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioData, setAudioData] = useState<string | null>(null);
  const [sentiment, setSentiment] = useState<number | null>(0.79);
  const [location, setLocation] = useState<GeolocationCoordinates | null>(null);
  const [events, setEvents] = useState<{ time: Date; event: string }[]>([]);
  const { theme, setTheme } = useTheme();
  const mapRef = useRef(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [transcription, setTranscription] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const { complete, completion, isLoading } = useCompletion({
    api: "/api/completion",
  });

  useEffect(() => {
    if ("geolocation" in navigator) {
      const id = navigator.geolocation.watchPosition(
        (position) => setLocation(position.coords),
        (error) => console.error("Error getting location:", error),
        { enableHighAccuracy: true }
      );
      return () => navigator.geolocation.clearWatch(id);
    }
  }, []);

  useEffect(() => {
    if (location && mapRef.current) {
      // @ts-ignore
      mapRef.current.flyTo({
        center: [location.longitude, location.latitude],
        zoom: 14,
      });
    }
  }, [location]);

  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      mediaRecorderRef.current.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setAudioBlob(blob);
        transcribeAudio(blob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      addEvent("Started recording");
    } catch (error) {
      console.error("Error starting recording:", error);
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      addEvent("Stopped recording");
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    const url = URL.createObjectURL(audioBlob);
    setAudioUrl(url);

    try {
      console.log("Transcribing audio...");
      
      // Create a FormData object to send the file
      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio.webm');

      // Send the audio file to your server endpoint
      const response = await fetch('/api/transcribe', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Transcription failed');
      }

      const { transcript } = await response.json();
      console.log(transcript);

      setTranscription(transcript);
      
      // After transcription, call the completion API
      complete("Summarize the following emergency call: " + transcript);
    } catch (error) {
      console.error("Error transcribing audio:", error);
      setTranscription("Error transcribing audio. Please try again.");
    }
  };

  const handleSubmit = () => {
    // Here you would typically send the data to a backend service
    addEvent("Submitted information to police");
    alert("Emergency information submitted to the police.");
  };

  const addEvent = (event: string) => {
    setEvents((prev) => [...prev, { time: new Date(), event }]);
  };

  return (
    <div className="flex h-screen justify-center items-center">
      <Card className="w-full max-w-4xl">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-2xl font-bold text-teal-600">
            Emergency Response System
          </CardTitle>
          <div>
            <img src="https://replicate.delivery/yhqm/oTNwk1Txx6oQCxjg0HGtCUNDXEo8HJ4DxPswJ7nyquIp6Q3E/out-0.webp" width="75" height="75"/>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex justify-center space-x-4">
            <Button
              onClick={handleStartRecording}
              disabled={isRecording}
              size="lg"
              variant={isRecording ? "destructive" : "default"}
              className="w-24 h-24 rounded-full"
            >
              <Mic className="w-12 h-12" />
              <span className="sr-only">
                {isRecording ? "Recording in progress" : "Start recording"}
              </span>
            </Button>
            {isRecording && (
              <Button
                onClick={handleStopRecording}
                size="lg"
                variant="outline"
                className="w-24 h-24 rounded-full"
              >
                <Square className="w-12 h-12" />
                <span className="sr-only">Stop recording</span>
              </Button>
            )}
          </div>
          {isRecording && (
            <div className="text-center" aria-live="polite">
              <p className="text-sm text-muted-foreground">
                Recording in progress...
              </p>
              <Progress value={33} className="w-full mt-2" />
            </div>
          )}
          {audioUrl && (
            <div className="mt-4">
              <h3 className="text-lg font-semibold mb-2">Recorded Audio</h3>
              <audio src={audioUrl} controls className="w-full" />
            </div>
          )}
          <Tabs defaultValue="map" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="map">Map</TabsTrigger>
              <TabsTrigger value="sentiment">Sentiment</TabsTrigger>
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
            </TabsList>
            <TabsContent value="map">
              <div className="w-full h-[400px] rounded-md overflow-hidden">
                {location ? (
                  <Map
                    ref={mapRef}
                    mapboxAccessToken={MAPBOX_ACCESS_TOKEN}
                    initialViewState={{
                      longitude: location.longitude,
                      latitude: location.latitude,
                      zoom: 14,
                    }}
                    style={{ width: "100%", height: "100%" }}
                    mapStyle="mapbox://styles/mapbox/streets-v11"
                  >
                    <Marker
                      longitude={location.longitude}
                      latitude={location.latitude}
                      color="red"
                    />
                  </Map>
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-muted">
                    <p className="text-blue-600">
                      Location data not available
                    </p>
                  </div>
                )}
              </div>
              {location && (
                <div className="mt-2 text-sm">
                  <p>
                    <MapPin className="inline-block mr-1" />
                    Latitude: {location.latitude.toFixed(6)}, Longitude:{" "}
                    {location.longitude.toFixed(6)}
                  </p>
                  <p className="text-blue-600">
                    Accuracy: ±{location.accuracy.toFixed(2)} meters
                  </p>
                </div>
              )}
            </TabsContent>
            <TabsContent value="sentiment">
              {sentiment !== null ? (
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold">Sentiment Analysis</h3>
                  <div className="flex items-center space-x-2">
                    <Progress value={sentiment * 100} className="w-full" />
                    <span className="text-sm font-medium">
                      {(sentiment * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-sm text-center text-muted-foreground">
                    {sentiment < 0.3
                      ? "Negative"
                      : sentiment < 0.7
                      ? "Neutral"
                      : "Positive"}
                  </p>
                </div>
              ) : (
                <p className="text-center text-muted-foreground">
                  No sentiment data available
                </p>
              )}
            </TabsContent>
            <TabsContent value="summary">
              {completion ? (
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold">Summarized Notes</h3>
                  <Textarea
                    value={completion}
                    readOnly
                    className="w-full h-32"
                  />
                  {transcription && (
                    <div>
                      <h4 className="text-md font-semibold mt-4">Transcription</h4>
                      <p className="text-sm">{transcription}</p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-center text-muted-foreground">
                  Speaker sounds excited. Speaker is greeting Hack The North.
                </p>
              )}
            </TabsContent>
            <TabsContent value="timeline">
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">Event Timeline</h3>
                <ul className="space-y-2">
                  {events.map((event, index) => (
                    <li key={index} className="text-sm">
                      <span className="font-medium">
                        {event.time.toLocaleTimeString()}
                      </span>
                      : {event.event}
                    </li>
                  ))}
                </ul>
              </div>
            </TabsContent>
          </Tabs>
          <div className="flex justify-center">
            <Button
              onClick={handleSubmit}
              className={cn(
                "w-full max-w-xs",
                audioBlob
                  ? "bg-red-500 hover:bg-red-600"
                  : "bg-muted text-muted-foreground"
              )}
              disabled={!audioBlob}
            >
              <AlertTriangle className="w-4 h-4 mr-2" />
              Submit to Police
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
